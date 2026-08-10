"""Імпорт товарів постачальника: валідація рядків і збереження з savepoint."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, BinaryIO

from django.db import IntegrityError, transaction

from src.catalog.models import Category, Product, Supplier, make_slug
from src.catalog.services.supplier_import_parsers import (
    SupplierImportParseError,
    parse_supplier_file,
)

logger = logging.getLogger('catalog.supplier_import')


@dataclass
class ImportRowError:
    row: int
    sku: str
    message: str


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[ImportRowError] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def summary(self) -> str:
        return (
            f'Створено: {self.created}, оновлено: {self.updated}, '
            f'пропущено: {self.skipped}, помилок: {self.error_count}'
        )


@dataclass
class _ValidatedRow:
    row_number: int
    sku: str
    name: str | None
    price: Decimal | None
    stock: int | None
    category: Category | None
    category_provided: bool


def _parse_price(raw: str) -> Decimal:
    text = (raw or '').strip().replace(' ', '').replace(',', '.')
    if not text:
        raise ValueError('Ціна обовʼязкова')
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f'Некоректна ціна: {raw!r}') from exc
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
        raise ValueError(f'Некоректний залишок: {raw!r}') from exc
    if as_decimal < 0:
        raise ValueError('Залишок не може бути відʼємним')
    if as_decimal != as_decimal.to_integral_value():
        raise ValueError('Залишок має бути цілим числом')
    return int(as_decimal)


def _resolve_category(raw: str) -> Category | None:
    text = (raw or '').strip()
    if not text:
        return None
    category = Category.objects.filter(name__iexact=text).first()
    if category:
        return category
    return Category.objects.filter(slug__iexact=text).first()


def _unique_product_slug(name: str, exclude_pk: int | None = None) -> str:
    product = Product(name=name, pk=exclude_pk)
    return make_slug(product, source_field='name')


def _validate_rows(
    raw_rows: list[dict[str, str]],
    *,
    default_category: Category | None,
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

        if not sku:
            report.errors.append(ImportRowError(index, '', 'Відсутній SKU'))
            continue

        if sku in seen_skus:
            report.errors.append(
                ImportRowError(
                    index,
                    sku,
                    f'Дублікат SKU у файлі (перший рядок {seen_skus[sku]})',
                ),
            )
            continue
        seen_skus[sku] = index

        existing = Product.objects.filter(sku=sku).only('pk').first()
        is_create = existing is None

        name: str | None = name_raw or None
        if is_create and not name:
            report.errors.append(
                ImportRowError(index, sku, 'Для нового товару потрібна назва'),
            )
            continue

        price: Decimal | None = None
        if price_raw or is_create:
            try:
                price = _parse_price(price_raw)
            except (InvalidOperation, ValueError) as exc:
                report.errors.append(ImportRowError(index, sku, str(exc)))
                continue

        stock: int | None
        try:
            stock = _parse_stock(stock_raw)
        except ValueError as exc:
            report.errors.append(ImportRowError(index, sku, str(exc)))
            continue
        if is_create and stock is None:
            stock = 0

        category: Category | None = None
        category_provided = bool(category_raw)
        if category_provided:
            category = _resolve_category(category_raw)
            if category is None:
                report.errors.append(
                    ImportRowError(
                        index,
                        sku,
                        f'Категорію не знайдено: {category_raw!r}',
                    ),
                )
                continue
        elif is_create:
            if default_category is None:
                report.errors.append(
                    ImportRowError(
                        index,
                        sku,
                        'Немає категорії в рядку і не задано категорію за замовчуванням',
                    ),
                )
                continue
            category = default_category

        validated.append(
            _ValidatedRow(
                row_number=index,
                sku=sku,
                name=name,
                price=price,
                stock=stock,
                category=category,
                category_provided=category_provided,
            ),
        )

    return validated, report


def _persist_row(row: _ValidatedRow, supplier: Supplier) -> str:
    """Створює або оновлює товар. Повертає 'created' | 'updated'."""
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
            is_active=True,
        )
        product.save()
        return 'created'

    if row.name:
        product.name = row.name
    if row.price is not None:
        product.price = row.price
    if row.stock is not None:
        product.stock_quantity = row.stock
    if row.category_provided and row.category is not None:
        product.category = row.category
    product.supplier = supplier
    product.save()
    return 'updated'


def import_supplier_file(
    *,
    supplier: Supplier,
    file_obj: BinaryIO,
    filename: str,
    default_category: Category | None = None,
) -> ImportReport:
    """
    Парсить файл постачальника, валідує рядки і зберігає товари.

    Кожен валідний рядок зберігається у власному savepoint всередині atomic(),
    тож помилка одного рядка не відкочує успішні.
    """
    logger.info(
        'Supplier import start supplier_id=%s file=%s',
        supplier.pk,
        filename,
    )

    try:
        raw_rows = parse_supplier_file(file_obj, filename)
    except SupplierImportParseError:
        raise

    validated, report = _validate_rows(raw_rows, default_category=default_category)

    with transaction.atomic():
        for row in validated:
            try:
                with transaction.atomic():
                    action = _persist_row(row, supplier)
            except IntegrityError as exc:
                logger.exception(
                    'IntegrityError on sku=%s row=%s',
                    row.sku,
                    row.row_number,
                )
                report.errors.append(
                    ImportRowError(row.row_number, row.sku, f'Помилка БД: {exc}'),
                )
                report.skipped += 1
                continue
            except Exception as exc:  # noqa: BLE001 — звіт по рядку, без крашу імпорту
                logger.exception(
                    'Unexpected error on sku=%s row=%s',
                    row.sku,
                    row.row_number,
                )
                report.errors.append(
                    ImportRowError(row.row_number, row.sku, f'Помилка: {exc}'),
                )
                report.skipped += 1
                continue

            if action == 'created':
                report.created += 1
            else:
                report.updated += 1

    logger.info(
        'Supplier import done supplier_id=%s %s',
        supplier.pk,
        report.summary(),
    )
    return report
