"""Імпорт товарів постачальника: валідація рядків і збереження з savepoint."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import BinaryIO

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction

from src.catalog.models import Category, Product, ProductImage, Supplier, make_slug
from src.catalog.services.supplier_import_parsers import (
    SupplierImportParseError,
    parse_supplier_file,
)
from src.catalog.siker_yml import download_image, safe_image_filename

logger = logging.getLogger('catalog.supplier_import')

IMPORT_FALLBACK_SLUG = 'import-bez-kategorii'
IMPORT_FALLBACK_NAME = 'Імпорт / Без категорії'
IMPORT_FALLBACK_EXTERNAL_ID = 'oyra:import-fallback'

# Захист від "вигрузок-простирадл" з десятками фото на товар — цього достатньо
# для будь-якої реальної галереї, а імпорт великого файлу лишається швидким.
MAX_IMAGES_PER_PRODUCT = 20


@dataclass
class ImportRowError:
    row: int
    sku: str
    message: str
    hint: str = ''


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    fallback_category_used: int = 0
    images_added: int = 0
    images_failed: int = 0
    errors: list[ImportRowError] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def summary(self) -> str:
        text = (
            f'Створено: {self.created}, оновлено: {self.updated}, '
            f'пропущено: {self.skipped}, помилок: {self.error_count}'
        )
        if self.fallback_category_used:
            text += (
                f'. Потрібно розкласти по категоріях: {self.fallback_category_used}'
            )
        if self.images_added:
            text += f'. Завантажено фото: {self.images_added}'
        if self.images_failed:
            text += f' (не вдалося завантажити: {self.images_failed})'
        return text


def _row_error(
    row: int,
    sku: str,
    message: str,
    hint: str = '',
) -> ImportRowError:
    return ImportRowError(row=row, sku=sku, message=message, hint=hint)


@dataclass
class _ValidatedRow:
    row_number: int
    sku: str
    name: str | None
    price: Decimal | None
    stock: int | None
    category: Category | None
    category_provided: bool
    description: str | None
    image_urls: list[str] = field(default_factory=list)
    used_fallback: bool = False


def get_import_fallback_category() -> Category:
    """
    Службова категорія для нових товарів без збігу з каталогом.

    is_active=False — товари не показуються на вітрині, доки менеджер
    не перенесе їх у звичайну категорію.
    """
    category, created = Category.objects.get_or_create(
        slug=IMPORT_FALLBACK_SLUG,
        defaults={
            'name': IMPORT_FALLBACK_NAME,
            'parent': None,
            'is_active': False,
            'external_id': IMPORT_FALLBACK_EXTERNAL_ID,
            'sort_order': 9999,
        },
    )
    if created:
        logger.info('Created import fallback category id=%s', category.pk)
    return category


def _parse_price(raw: str) -> Decimal:
    text = (raw or '').strip().replace(' ', '').replace(',', '.')
    if not text:
        raise ValueError('Немає ціни')
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f'Ціна має бути числом (зараз: «{raw}»)') from exc
    if value < 0:
        raise ValueError('Ціна не може бути відʼємною')
    return value.quantize(Decimal('0.01'))


def _parse_stock(raw: str) -> int | None:
    text = (raw or '').strip()
    if not text:
        return None
    text = text.replace(' ', '').replace(',', '.')
    try:
        as_decimal = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(
            f'Залишок (Наличие) має бути цілим числом (зараз: «{raw}»)',
        ) from exc
    if as_decimal < 0:
        raise ValueError('Залишок не може бути відʼємним')
    if as_decimal != as_decimal.to_integral_value():
        raise ValueError(
            f'Залишок має бути цілим числом без дробової частини (зараз: «{raw}»)',
        )
    return int(as_decimal)


def _parse_image_urls(raw: str) -> list[str]:
    """
    Розбирає колонку «Ссылка_изображения» (Prom/Siker пише кілька URL через кому).

    Без цього фото з вигрузки ігнорувались повністю — товар зберігався
    без жодної картинки, хоча посилання в файлі були коректні.
    """
    text = (raw or '').strip()
    if not text:
        return []

    urls: list[str] = []
    seen: set[str] = set()
    for chunk in text.split(','):
        url = chunk.strip()
        if not url or url in seen:
            continue
        if not url.lower().startswith(('http://', 'https://')):
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) >= MAX_IMAGES_PER_PRODUCT:
            break
    return urls


def _resolve_category(raw: str) -> Category | None:
    """Спочатку активні категорії (уникаємо дублів зі старих імпортів)."""
    text = (raw or '').strip()
    if not text:
        return None

    active = Category.objects.filter(is_active=True)
    category = active.filter(name__iexact=text).first()
    if category:
        return category
    category = active.filter(slug__iexact=text).first()
    if category:
        return category

    inactive = Category.objects.filter(is_active=False).exclude(
        slug=IMPORT_FALLBACK_SLUG,
    )
    category = inactive.filter(name__iexact=text).first()
    if category:
        return category
    return inactive.filter(slug__iexact=text).first()


def _unique_product_slug(name: str, exclude_pk: int | None = None) -> str:
    product = Product(name=name, pk=exclude_pk)
    return make_slug(product, source_field='name')


def _validate_rows(
    raw_rows: list[dict[str, str]],
    *,
    fallback_category: Category,
) -> tuple[list[_ValidatedRow], ImportReport]:
    report = ImportReport()
    validated: list[_ValidatedRow] = []
    seen_skus: dict[str, int] = {}

    for index, raw in enumerate(raw_rows, start=2):
        sku = (raw.get('sku') or '').strip()
        name_raw = (raw.get('name') or '').strip()
        price_raw = (raw.get('price') or '').strip()
        stock_raw = (raw.get('stock') or '').strip()
        category_raw = (raw.get('category') or '').strip()
        description_raw = (raw.get('description') or '').strip()
        images_raw = (raw.get('images') or '').strip()

        if not sku:
            report.errors.append(
                _row_error(
                    index,
                    '',
                    'У рядку немає артикула (SKU / Код_товара).',
                    'Додайте код товару в колонку «Код_товара» або видаліть порожній рядок.',
                ),
            )
            continue

        if sku in seen_skus:
            report.errors.append(
                _row_error(
                    index,
                    sku,
                    f'Цей артикул уже є в файлі вище (рядок {seen_skus[sku]}).',
                    'Залиште лише один рядок з цим кодом або змініть дублікат.',
                ),
            )
            continue
        seen_skus[sku] = index

        existing = Product.objects.filter(sku=sku).only('pk').first()
        is_create = existing is None

        name: str | None = name_raw or None
        if is_create and not name:
            report.errors.append(
                _row_error(
                    index,
                    sku,
                    'Новий товар без назви.',
                    'Заповніть «Название_позиции_укр» (або перемкніть мову імпорту) '
                    'і спробуйте знову.',
                ),
            )
            continue

        price: Decimal | None = None
        if price_raw or is_create:
            try:
                price = _parse_price(price_raw)
            except (InvalidOperation, ValueError) as exc:
                report.errors.append(
                    _row_error(
                        index,
                        sku,
                        str(exc),
                        'Виправте колонку «Цена»: лише число, наприклад 1999 або 1999.50.',
                    ),
                )
                continue

        stock: int | None
        try:
            stock = _parse_stock(stock_raw)
        except ValueError as exc:
            report.errors.append(
                _row_error(
                    index,
                    sku,
                    str(exc),
                    'Виправте колонку «Наличие»: ціле число на кшталт 0, 1, 10.',
                ),
            )
            continue
        if is_create and stock is None:
            stock = 0

        category: Category | None = None
        category_provided = False
        used_fallback = False

        if category_raw:
            resolved = _resolve_category(category_raw)
            if resolved is not None:
                category = resolved
                category_provided = True
            elif is_create:
                category = fallback_category
                used_fallback = True
        elif is_create:
            category = fallback_category
            used_fallback = True

        validated.append(
            _ValidatedRow(
                row_number=index,
                sku=sku,
                name=name,
                price=price,
                stock=stock,
                category=category,
                category_provided=category_provided,
                description=description_raw or None,
                image_urls=_parse_image_urls(images_raw),
                used_fallback=used_fallback,
            ),
        )

    return validated, report


def _attach_missing_images(product: Product, image_urls: list[str]) -> tuple[int, int]:
    """
    Довантажує фото за URL з вигрузки, якщо товар ще без жодної картинки.

    Товари з наявною галереєю не чіпаємо — повторний імпорт того самого
    файлу не повинен створювати дублікати фото.
    Повертає (додано, помилок).
    """
    if not image_urls or product.images.exists():
        return 0, 0

    added = 0
    failed = 0
    for order, url in enumerate(image_urls):
        try:
            data, filename = download_image(url)
        except Exception:  # noqa: BLE001 — мережева помилка не має валити імпорт
            logger.warning(
                'Не вдалося завантажити фото sku=%s url=%s',
                product.sku,
                url,
                exc_info=True,
            )
            failed += 1
            continue
        if not data:
            failed += 1
            continue

        safe_name = safe_image_filename(product.sku, order, filename)
        image = ProductImage(
            product=product,
            alt_text=product.name[:200],
            sort_order=order,
            is_main=(order == 0),
        )
        image.image.save(safe_name, ContentFile(data), save=True)
        added += 1
    return added, failed


def _persist_row(row: _ValidatedRow, supplier: Supplier) -> tuple[str, int, int]:
    """Створює або оновлює товар. Повертає ('created'|'updated', фото_додано, фото_помилок)."""
    product = Product.objects.filter(sku=row.sku).first()
    if product is None:
        assert row.name is not None
        assert row.price is not None
        assert row.category is not None
        product = Product(
            sku=row.sku,
            name=row.name,
            slug=_unique_product_slug(row.name),
            price=row.price,
            category=row.category,
            supplier=supplier,
            stock_quantity=row.stock if row.stock is not None else 0,
            description=row.description or '',
            is_active=True,
        )
        product.save()
        images_added, images_failed = _attach_missing_images(product, row.image_urls)
        return 'created', images_added, images_failed

    if row.name:
        product.name = row.name
    if row.price is not None:
        product.price = row.price
    if row.stock is not None:
        product.stock_quantity = row.stock
    if row.category_provided and row.category is not None:
        product.category = row.category
    if row.description:
        product.description = row.description
    product.supplier = supplier
    product.save()
    images_added, images_failed = _attach_missing_images(product, row.image_urls)
    return 'updated', images_added, images_failed


def import_supplier_file(
    *,
    supplier: Supplier,
    file_obj: BinaryIO,
    filename: str,
    name_locale: str = 'uk',
) -> ImportReport:
    """
    Парсить файл постачальника, валідує рядки і зберігає товари.

    Категорія з файлу матчиться автоматично; якщо збігу немає —
    новий товар потрапляє в «Імпорт / Без категорії».
    """
    locale = 'ru' if name_locale == 'ru' else 'uk'
    logger.info(
        'Supplier import start supplier_id=%s file=%s locale=%s',
        supplier.pk,
        filename,
        locale,
    )

    try:
        raw_rows = parse_supplier_file(
            file_obj,
            filename,
            name_locale=locale,  # type: ignore[arg-type]
        )
    except SupplierImportParseError:
        raise

    fallback_category = get_import_fallback_category()
    validated, report = _validate_rows(
        raw_rows,
        fallback_category=fallback_category,
    )

    with transaction.atomic():
        for row in validated:
            try:
                with transaction.atomic():
                    action, images_added, images_failed = _persist_row(row, supplier)
            except IntegrityError:
                logger.exception(
                    'IntegrityError on sku=%s row=%s',
                    row.sku,
                    row.row_number,
                )
                report.errors.append(
                    _row_error(
                        row.row_number,
                        row.sku,
                        'Не вдалося зберегти товар у базі (конфлікт даних).',
                        'Перевірте, чи немає іншого товару з таким самим артикулом '
                        'або схожою назвою/посиланням. Збережіть файл і зверніться '
                        'до адміністратора, якщо помилка повториться.',
                    ),
                )
                report.skipped += 1
                continue
            except Exception:  # noqa: BLE001 — звіт по рядку, без крашу імпорту
                logger.exception(
                    'Unexpected error on sku=%s row=%s',
                    row.sku,
                    row.row_number,
                )
                report.errors.append(
                    _row_error(
                        row.row_number,
                        row.sku,
                        'Неочікувана помилка під час збереження рядка.',
                        'Спробуйте імпортувати файл ще раз. Якщо не допоможе — '
                        'надішліть файл адміністратору.',
                    ),
                )
                report.skipped += 1
                continue
            if action == 'created':
                report.created += 1
                if row.used_fallback:
                    report.fallback_category_used += 1
            else:
                report.updated += 1
            report.images_added += images_added
            report.images_failed += images_failed

    logger.info(
        'Supplier import done supplier_id=%s %s',
        supplier.pk,
        report.summary(),
    )
    return report
