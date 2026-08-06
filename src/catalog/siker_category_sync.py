"""Синхронізація дерева категорій з YML Siker (збереження parentId)."""
from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from slugify import slugify

from src.catalog.models import Category, Product
from src.catalog.siker_website_layout import apply_siker_website_layout
from src.catalog.siker_yml import YmlCategory, YmlOffer

# Корені, які ховаємо (можна повернути пізніше через is_active=True).
HIDDEN_ROOT_NAMES = frozenset({
    'трактори',
    'обладнання для сто',
    'обладнання сто',
    'акумуляторні батареї',
    'сертифікат',
})


@dataclass
class SyncStats:
    categories_upserted: int = 0
    categories_hidden: int = 0
    layout_reparented: int = 0
    products_remapped: int = 0
    products_skipped: int = 0


def _is_hidden_root_name(name: str) -> bool:
    return (name or '').strip().lower() in HIDDEN_ROOT_NAMES


def _unique_slug(base: str, exclude_pk: int | None = None) -> str:
    slug = base[:200] or 'category'
    candidate = slug
    n = 1
    while True:
        qs = Category.objects.filter(slug=candidate)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        if not qs.exists():
            return candidate
        n += 1
        suffix = f'-{n}'
        candidate = f'{slug[: 220 - len(suffix)]}{suffix}'


def build_category_tree(
    yml_categories: list[YmlCategory],
) -> dict[str, Category]:
    """
    Upsert категорій за external_id з точним parent.
    Унікальний slug: name + external_id (уникає колізій «Велика»/«Середня»).
    """
    by_ext: dict[str, Category] = {}
    pending = list(yml_categories)
    guard = 0
    while pending and guard < 40:
        guard += 1
        next_pending: list[YmlCategory] = []
        for item in pending:
            parent = None
            if item.parent_id:
                parent = by_ext.get(item.parent_id)
                if parent is None:
                    next_pending.append(item)
                    continue

            cat = Category.objects.filter(external_id=item.external_id).first()
            slug_base = slugify(item.name) or f'cat-{item.external_id}'
            # Зовнішній id у slug гарантує унікальність одноіменних гілок
            preferred = f'{slug_base}-{item.external_id}'[:220]

            if cat is None:
                # Міграція зі старого імпорту: той самий slug без id
                cat = Category.objects.filter(
                    external_id='',
                    name=item.name,
                    parent=parent,
                ).first()
            if cat is None and not item.parent_id:
                cat = Category.objects.filter(
                    external_id='',
                    name=item.name,
                    parent__isnull=True,
                ).first()

            if cat is None:
                cat = Category(
                    name=item.name,
                    slug=_unique_slug(preferred),
                    external_id=item.external_id,
                    parent=parent,
                    is_active=True,
                )
            else:
                cat.name = item.name
                cat.external_id = item.external_id
                cat.parent = parent
                if not cat.slug or cat.slug == slug_base:
                    cat.slug = _unique_slug(preferred, exclude_pk=cat.pk)

            cat.is_active = True
            lowered = item.name.lower()
            if 'спорт' in lowered or 'батут' in lowered or 'atleto' in lowered:
                cat.icon_key = 'sport'
            cat.save()
            by_ext[item.external_id] = cat

        pending = next_pending

    if pending:
        names = ', '.join(f'{p.name}({p.external_id})' for p in pending)
        raise ValueError(f'Не вдалося збудувати дерево категорій: {names}')

    return by_ext


def deactivate_hidden_branches(by_ext: dict[str, Category] | None = None) -> int:
    """Приховує Трактори / Обладнання СТО та всіх нащадків (будь-який рівень)."""
    matches = [
        cat for cat in Category.objects.all()
        if _is_hidden_root_name(cat.name)
    ]
    # Спочатку корені гілок (без предка, який теж у matches)
    match_ids = {c.pk for c in matches}
    roots = []
    for cat in matches:
        parent = cat.parent
        skip = False
        while parent is not None:
            if parent.pk in match_ids:
                skip = True
                break
            parent = parent.parent
        if not skip:
            roots.append(cat)

    hidden = 0
    for root in roots:
        ids = _collect_descendant_ids(root)
        updated = Category.objects.filter(pk__in=ids).update(is_active=False)
        hidden += updated
    return hidden


def _collect_descendant_ids(root: Category) -> list[int]:
    stack = [root]
    ids: list[int] = []
    while stack:
        node = stack.pop()
        ids.append(node.pk)
        stack.extend(list(node.children.all()))
    return ids

def remap_products_from_offers(
    offers: list[YmlOffer],
    cat_map: dict[str, Category],
) -> tuple[int, int]:
    """Переприв'язує товари до leaf-категорій з YML за SKU (vendor_code)."""
    remapped = 0
    skipped = 0
    sku_to_cat: dict[str, Category] = {}
    for offer in offers:
        cat = cat_map.get(offer.category_id)
        if cat is None:
            skipped += 1
            continue
        code = (offer.vendor_code or '').strip()
        if code:
            sku_to_cat[code] = cat

    if not sku_to_cat:
        return 0, skipped

    products = Product.objects.filter(sku__in=sku_to_cat.keys()).only('pk', 'sku', 'category_id')
    to_update: list[Product] = []
    for product in products:
        target = sku_to_cat.get(product.sku)
        if target and product.category_id != target.pk:
            product.category = target
            to_update.append(product)
    if to_update:
        Product.objects.bulk_update(to_update, ['category'])
        remapped = len(to_update)
    return remapped, skipped


@transaction.atomic
def sync_categories_and_products(
    yml_categories: list[YmlCategory],
    offers: list[YmlOffer],
) -> SyncStats:
    stats = SyncStats()
    cat_map = build_category_tree(yml_categories)
    stats.categories_upserted = len(cat_map)
    # YML parentId ≠ меню siker.ua — вирівнюємо дерево під сайт
    layout = apply_siker_website_layout(cat_map)
    stats.layout_reparented = layout.reparented
    # Оновлюємо map після layout (нові oyra:* корені)
    for cat in Category.objects.exclude(external_id=''):
        cat_map[cat.external_id] = cat
    stats.categories_hidden = deactivate_hidden_branches(cat_map)
    # Seed без id — ховаємо; синтетичні oyra:* лишаємо
    stale_qs = Category.objects.filter(external_id='')
    stale = stale_qs.update(is_active=False)
    stats.categories_hidden += stale
    remapped, skipped = remap_products_from_offers(offers, cat_map)
    stats.products_remapped = remapped
    stats.products_skipped = skipped
    return stats
