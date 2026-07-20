"""Разовий імпорт товарів з YML-вигрузки Siker."""
from __future__ import annotations

import mimetypes
import re
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.signals import post_save
from slugify import slugify

from src.accounts.models import WishlistItem
from src.catalog.models import (
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductImage,
    make_slug,
)
from src.catalog.signals import product_image_to_webp
from src.catalog.siker_yml import (
    DEFAULT_EXPORT_URL,
    download_image,
    html_to_plain,
    load_yml_bytes,
    parse_yml,
)
from src.orders.models import OrderItem
from src.reviews.models import Review

_SAFE_NAME_RE = re.compile(r'[^a-zA-Z0-9._-]+')


class Command(BaseCommand):
    help = (
        'Імпорт товарів/категорій/фото з YML Siker. '
        'За замовчуванням повністю замінює каталог товарів.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            default=DEFAULT_EXPORT_URL,
            help=f'URL вигрузки (за замовчуванням: {DEFAULT_EXPORT_URL})',
        )
        parser.add_argument(
            '--file',
            default='',
            help='Локальний шлях до .yml замість URL',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Лише розбір і статистика, без запису в БД',
        )
        parser.add_argument(
            '--keep-old-categories',
            action='store_true',
            help='Не видаляти старі категорії без товарів',
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Не завантажувати фото (швидкий тест)',
        )
        parser.add_argument(
            '--no-webp',
            action='store_true',
            help='Вимкнути конвертацію фото в WebP під час імпорту',
        )

    def handle(self, *args, **options):
        url = options['url']
        file_path = (options['file'] or '').strip() or None
        dry_run = options['dry_run']
        skip_images = options['skip_images']
        no_webp = options['no_webp']

        self.stdout.write('Завантаження YML…')
        try:
            raw = load_yml_bytes(source=url, file_path=file_path)
            catalog = parse_yml(raw)
        except Exception as exc:
            raise CommandError(f'Не вдалося прочитати YML: {exc}') from exc

        self.stdout.write(
            f'Магазин: {catalog.shop_name}; '
            f'категорій: {len(catalog.categories)}; '
            f'товарів: {len(catalog.offers)}'
        )
        if not catalog.offers:
            raise CommandError('У вигрузці немає товарів (offers)')

        if dry_run:
            pics = sum(len(o.pictures) for o in catalog.offers)
            self.stdout.write(self.style.WARNING(
                f'DRY-RUN: буде імпортовано {len(catalog.offers)} товарів, '
                f'{pics} фото. БД не змінено.'
            ))
            return

        if no_webp:
            post_save.disconnect(product_image_to_webp, sender=ProductImage)

        try:
            with transaction.atomic():
                archived = self._purge_catalog(
                    keep_categories=options['keep_old_categories'],
                )
                cat_map = self._import_categories(catalog.categories)

            stats = self._import_offers(
                catalog.offers,
                cat_map,
                skip_images=skip_images,
            )
            stats['archived'] = archived
        finally:
            if no_webp:
                post_save.connect(product_image_to_webp, sender=ProductImage)

        self.stdout.write(self.style.SUCCESS(
            f'Готово: створено {stats["products"]} товарів, '
            f'{stats["images"]} фото, '
            f'пропущено {stats["skipped"]}, '
            f'архівовано через замовлення {stats["archived"]}.'
        ))

    def _purge_catalog(self, keep_categories: bool) -> int:
        protected_ids = set(
            OrderItem.objects.values_list('product_id', flat=True).distinct()
        )
        archived = 0
        if protected_ids:
            for product in Product.objects.filter(pk__in=protected_ids):
                product.is_active = False
                if not product.sku.startswith(f'archived-{product.pk}-'):
                    product.sku = f'archived-{product.pk}-{product.sku}'[:80]
                if not product.slug.startswith(f'archived-{product.pk}-'):
                    product.slug = f'archived-{product.pk}-{product.slug}'[:320]
                product.save(update_fields=['is_active', 'sku', 'slug', 'updated_at'])
                archived += 1
            self.stdout.write(self.style.WARNING(
                f'Залишено {archived} товарів з історії замовлень (PROTECT).'
            ))

        deletable = Product.objects.exclude(pk__in=protected_ids)
        count = deletable.count()
        WishlistItem.objects.filter(product__in=deletable).delete()
        Review.objects.filter(product__in=deletable).delete()
        for img in ProductImage.objects.filter(product__in=deletable).iterator():
            img.image.delete(save=False)
        deletable.delete()
        self.stdout.write(f'Видалено товарів: {count}')

        if not keep_categories:
            empty = Category.objects.filter(products__isnull=True)
            removed = 0
            for cat in list(empty.order_by('-id')):
                if cat.products.exists() or cat.children.exists():
                    continue
                cat.delete()
                removed += 1
            self.stdout.write(f'Видалено порожніх категорій: {removed}')
        return archived

    def _import_categories(self, categories) -> dict[str, Category]:
        by_ext: dict[str, Category] = {}
        # Батьки раніше дітей: кілька проходів
        pending = list(categories)
        guard = 0
        while pending and guard < 20:
            guard += 1
            next_pending = []
            for item in pending:
                parent = None
                if item.parent_id:
                    parent = by_ext.get(item.parent_id)
                    if parent is None:
                        next_pending.append(item)
                        continue
                slug_base = slugify(item.name) or f'cat-{item.external_id}'
                # Унікальний slug у межах всього дерева
                cat = Category.objects.filter(slug=slug_base).first()
                if cat is None:
                    cat = Category(name=item.name, slug=slug_base)
                    # make_slug з allow_unicode у моделі — форсимо латинський slug
                    base = slug_base
                    slug = base
                    n = 1
                    while Category.objects.filter(slug=slug).exists():
                        slug = f'{base}-{n}'
                        n += 1
                    cat.slug = slug
                cat.name = item.name
                cat.parent = parent
                cat.is_active = True
                lowered = item.name.lower()
                if 'спорт' in lowered or 'батут' in lowered or 'atleto' in lowered:
                    cat.icon_key = 'sport'
                cat.save()
                by_ext[item.external_id] = cat
            pending = next_pending

        if pending:
            names = ', '.join(p.name for p in pending)
            raise CommandError(f'Не вдалося збудувати дерево категорій: {names}')

        self.stdout.write(f'Категорій у мапі: {len(by_ext)}')
        return by_ext

    def _get_brand(self, name: str) -> Brand | None:
        name = (name or '').strip()
        if not name:
            return None
        slug = slugify(name, allow_unicode=True) or 'brand'
        brand, _ = Brand.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'is_active': True},
        )
        if brand.name != name:
            brand.name = name
            brand.is_active = True
            brand.save(update_fields=['name', 'is_active'])
        return brand

    def _import_offers(self, offers, cat_map, skip_images: bool) -> dict[str, int]:
        stats = {'products': 0, 'images': 0, 'skipped': 0, 'archived': 0}
        total = len(offers)

        for idx, offer in enumerate(offers, start=1):
            category = cat_map.get(offer.category_id)
            if category is None:
                self.stdout.write(self.style.WARNING(
                    f'[{idx}/{total}] пропуск {offer.vendor_code}: немає categoryId={offer.category_id}'
                ))
                stats['skipped'] += 1
                continue

            if Product.objects.filter(sku=offer.vendor_code).exists():
                # колізія з archived-* малоймовірна; пропускаємо дубль артикула
                self.stdout.write(self.style.WARNING(
                    f'[{idx}/{total}] пропуск: sku вже є ({offer.vendor_code})'
                ))
                stats['skipped'] += 1
                continue

            brand_name = offer.params.get('Виробник') or offer.params.get('Бренд') or ''
            brand = self._get_brand(brand_name)

            old_price = None
            if offer.price_drop is not None and offer.price_drop != offer.price:
                old_price = offer.price_drop

            product = Product(
                category=category,
                brand=brand,
                name=offer.name,
                sku=offer.vendor_code,
                short_description=html_to_plain(offer.description_html),
                description=offer.description_html,
                price=offer.price,
                old_price=old_price,
                availability=(
                    Product.AVAIL_IN_STOCK
                    if offer.available
                    else Product.AVAIL_OUT
                ),
                is_active=True,
                is_on_sale=bool(old_price),
            )
            product.slug = make_slug(product)
            product.save()

            attr_order = 0
            for pname, pvalue in offer.params.items():
                if pname.lower() in ('артикул',):
                    continue
                ProductAttribute.objects.create(
                    product=product,
                    name=pname,
                    value=pvalue[:255],
                    sort_order=attr_order,
                )
                attr_order += 1

            if not skip_images:
                stats['images'] += self._import_images(product, offer.pictures)

            stats['products'] += 1
            self.stdout.write(f'[{idx}/{total}] {product.sku} — {product.name[:60]}')

        return stats

    def _import_images(self, product: Product, urls: list[str]) -> int:
        saved = 0
        for order, url in enumerate(urls):
            try:
                data, filename = download_image(url)
            except Exception as exc:
                self.stdout.write(self.style.WARNING(
                    f'  фото помилка {url}: {exc}'
                ))
                continue
            if not data:
                continue

            safe = self._safe_filename(product.sku, order, filename)
            img = ProductImage(
                product=product,
                alt_text=product.name[:200],
                sort_order=order,
                is_main=(order == 0),
            )
            img.image.save(safe, ContentFile(data), save=True)
            saved += 1
        return saved

    @staticmethod
    def _safe_filename(sku: str, order: int, filename: str) -> str:
        """Коротке ім'я: ImageField за замовчуванням varchar(100), шлях products/ + ім'я."""
        suffix = PurePosixPath(filename).suffix.lower()
        if suffix not in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}:
            suffix = mimetypes.guess_extension('image/jpeg') or '.jpg'
        sku_part = _SAFE_NAME_RE.sub('-', sku)[:32]
        # products/ (~9) + ім'я ≈ до 50 символів — з запасом під WebP/унікалізацію storage
        return f'{sku_part}_{order}{suffix}'
