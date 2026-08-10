"""Парсери файлів постачальника: CSV, XLSX, JSON → list[dict]."""

from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any, BinaryIO, Mapping

logger = logging.getLogger('catalog.supplier_import')

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    'sku': ('sku', 'артикул', 'код_товара', 'код товара', 'vendor_code', 'vendorcode'),
    'name': ('name', 'title', 'назва', 'название'),
    'price': ('price', 'ціна', 'цена', 'цена рекомендова'),
    'stock': ('stock', 'stock_quantity', 'кількість', 'количество', 'остаток', 'qty', 'quantity'),
    'category': ('category', 'категорія', 'категория'),
}


class SupplierImportParseError(ValueError):
    """Некоректний формат або порожній файл імпорту."""


def _normalize_header(raw: Any) -> str:
    text = str(raw or '').strip().lower().replace('\ufeff', '')
    return ' '.join(text.replace('-', '_').split())


def _build_column_map(headers: list[str]) -> dict[str, str]:
    """Повертає mapping логічне_поле → оригінальний_заголовок."""
    normalized = {_normalize_header(h): h for h in headers if str(h or '').strip()}
    mapping: dict[str, str] = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            key = _normalize_header(alias)
            if key in normalized:
                mapping[field] = normalized[key]
                break
    return mapping


def _cell_str(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _rows_from_mappings(
    raw_rows: list[Mapping[str, Any]],
    column_map: dict[str, str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in raw_rows:
        mapped: dict[str, str] = {}
        for field, header in column_map.items():
            mapped[field] = _cell_str(raw.get(header))
        if any(mapped.values()):
            rows.append(mapped)
    return rows


def parse_csv(file_obj: BinaryIO | io.TextIOBase) -> list[dict[str, str]]:
    """Читає CSV (UTF-8 / UTF-8-SIG / cp1251 fallback) у нормалізовані рядки."""
    raw = file_obj.read()
    if isinstance(raw, bytes):
        for encoding in ('utf-8-sig', 'utf-8', 'cp1251'):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise SupplierImportParseError('Не вдалося декодувати CSV (UTF-8 / cp1251).')
    else:
        text = raw

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise SupplierImportParseError('CSV без заголовків.')

    headers = [str(h) for h in reader.fieldnames if h is not None]
    column_map = _build_column_map(headers)
    if 'sku' not in column_map:
        raise SupplierImportParseError(
            'Не знайдено колонку SKU (sku / артикул / код_товара).',
        )

    raw_rows = [dict(row) for row in reader]
    rows = _rows_from_mappings(raw_rows, column_map)
    if not rows:
        raise SupplierImportParseError('CSV порожній або не містить даних.')
    return rows


def parse_xlsx(file_obj: BinaryIO) -> list[dict[str, str]]:
    """Читає перший аркуш XLSX через openpyxl."""
    try:
        import openpyxl
    except ImportError as exc:
        raise SupplierImportParseError(
            'Для .xlsx потрібен пакет openpyxl. Встановіть його або використайте CSV/JSON.',
        ) from exc

    workbook = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        if sheet is None:
            raise SupplierImportParseError('XLSX без активного аркуша.')

        iterator = sheet.iter_rows(values_only=True)
        try:
            header_row = next(iterator)
        except StopIteration as exc:
            raise SupplierImportParseError('XLSX порожній.') from exc

        headers = [_cell_str(h) for h in header_row]
        if not any(headers):
            raise SupplierImportParseError('XLSX без заголовків.')

        column_map = _build_column_map(headers)
        if 'sku' not in column_map:
            raise SupplierImportParseError(
                'Не знайдено колонку SKU (sku / артикул / код_товара).',
            )

        header_index = {h: i for i, h in enumerate(headers)}
        raw_rows: list[dict[str, Any]] = []
        for values in iterator:
            row_dict: dict[str, Any] = {}
            for header, idx in header_index.items():
                row_dict[header] = values[idx] if idx < len(values) else None
            raw_rows.append(row_dict)

        rows = _rows_from_mappings(raw_rows, column_map)
        if not rows:
            raise SupplierImportParseError('XLSX порожній або не містить даних.')
        return rows
    finally:
        workbook.close()


def parse_json(file_obj: BinaryIO | io.TextIOBase) -> list[dict[str, str]]:
    """
    Читає JSON.

    Підтримувані формати:
    - list[dict] з ключами-колонками
    - dict з ключем "products" / "items" / "rows"
    - dict sku → {name, price, ...}
    """
    raw = file_obj.read()
    if isinstance(raw, bytes):
        text = raw.decode('utf-8-sig')
    else:
        text = raw

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SupplierImportParseError(f'Некоректний JSON: {exc}') from exc

    if isinstance(payload, dict):
        for key in ('products', 'items', 'rows', 'data'):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
        else:
            # sku → object
            if payload and all(isinstance(v, dict) for v in payload.values()):
                converted: list[dict[str, Any]] = []
                for sku, data in payload.items():
                    item = dict(data)
                    item.setdefault('sku', sku)
                    converted.append(item)
                payload = converted
            else:
                raise SupplierImportParseError(
                    'JSON має бути масивом обʼєктів або обʼєктом products/items.',
                )

    if not isinstance(payload, list) or not payload:
        raise SupplierImportParseError('JSON порожній або не є масивом рядків.')

    if not all(isinstance(item, dict) for item in payload):
        raise SupplierImportParseError('Кожен елемент JSON має бути обʼєктом.')

    headers: list[str] = []
    seen: set[str] = set()
    for item in payload:
        for key in item.keys():
            key_s = str(key)
            if key_s not in seen:
                seen.add(key_s)
                headers.append(key_s)

    column_map = _build_column_map(headers)
    if 'sku' not in column_map:
        raise SupplierImportParseError(
            'Не знайдено поле SKU у JSON (sku / артикул / код_товара).',
        )

    rows = _rows_from_mappings(payload, column_map)
    if not rows:
        raise SupplierImportParseError('JSON не містить даних для імпорту.')
    return rows


def parse_supplier_file(file_obj: BinaryIO, filename: str) -> list[dict[str, str]]:
    """Визначає формат за розширенням і парсить файл."""
    name = (filename or '').lower().strip()
    logger.info('Parsing supplier file name=%s', name)

    if name.endswith('.csv'):
        return parse_csv(file_obj)
    if name.endswith('.xlsx'):
        return parse_xlsx(file_obj)
    if name.endswith('.json'):
        return parse_json(file_obj)

    raise SupplierImportParseError(
        'Підтримуються лише файли .csv, .xlsx або .json.',
    )
