"""Парсери файлів постачальника: CSV, XLSX, JSON → list[dict].

Підтримує як простий прайс, так і вигрузку Prom/Siker
(Код_товара, Название_позиции[_укр], Цена, Наличие, Название_группы).
"""

from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any, BinaryIO, Literal, Mapping

logger = logging.getLogger('catalog.supplier_import')

NameLocale = Literal['uk', 'ru']

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    'sku': (
        'sku',
        'артикул',
        'код_товара',
        'код товара',
        'vendor_code',
        'vendorcode',
    ),
    'price': (
        'price',
        'ціна',
        'цена',
        'цена рекомендова',
    ),
    'stock': (
        'stock',
        'stock_quantity',
        'кількість',
        'количество',
        'остаток',
        'наличие',
        'наявність',
        'qty',
        'quantity',
    ),
    'category': (
        'category',
        'категорія',
        'категория',
        'название_группы',
        'назва_групи',
        'название группы',
        'назва групи',
    ),
    'description': (
        'description',
        'опис',
        'описание',
    ),
    'images': (
        'images',
        'image',
        'image_url',
        'imageurl',
        'ссылка_изображения',
        'ссылки_изображений',
        'ссылка на изображение',
        'ссылка_на_изображение',
        'посилання_на_зображення',
        'посилання на зображення',
        'зображення',
        'изображение',
        'изображения',
        'фото',
        'photo',
        'picture',
        'pictures',
    ),
}

# Окремі aliases для назви: пріоритет залежить від мови сайту/імпорту.
NAME_ALIASES_UK: tuple[str, ...] = (
    'название_позиции_укр',
    'назва_позиції_укр',
    'назва_позиции_укр',
    'name_uk',
    'title_uk',
    'назва',
    'name',
    'title',
)
NAME_ALIASES_RU: tuple[str, ...] = (
    'название_позиции',
    'назва_позиції',
    'name_ru',
    'title_ru',
    'название',
    'name',
    'title',
)
DESCRIPTION_ALIASES_UK: tuple[str, ...] = (
    'описание_укр',
    'опис_укр',
    'description_uk',
    'опис',
    'описание',
    'description',
)
DESCRIPTION_ALIASES_RU: tuple[str, ...] = (
    'описание',
    'опис',
    'description_ru',
    'description',
)


class SupplierImportParseError(ValueError):
    """Некоректний формат або порожній файл імпорту."""


def _normalize_header(raw: Any) -> str:
    text = str(raw or '').strip().lower().replace('\ufeff', '')
    return ' '.join(text.replace('-', '_').split())


def _first_alias_hit(
    normalized_headers: dict[str, str],
    aliases: tuple[str, ...],
) -> str | None:
    for alias in aliases:
        key = _normalize_header(alias)
        if key in normalized_headers:
            return normalized_headers[key]
    return None


def _build_column_map(
    headers: list[str],
    *,
    name_locale: NameLocale = 'uk',
) -> dict[str, str]:
    """Повертає mapping логічне_поле → оригінальний_заголовок."""
    normalized = {_normalize_header(h): h for h in headers if str(h or '').strip()}
    mapping: dict[str, str] = {}

    for field, aliases in FIELD_ALIASES.items():
        if field == 'description':
            continue
        hit = _first_alias_hit(normalized, aliases)
        if hit:
            mapping[field] = hit

    name_aliases = NAME_ALIASES_UK if name_locale == 'uk' else NAME_ALIASES_RU
    # Fallback на іншу мову, якщо обраної колонки немає.
    fallback_name = NAME_ALIASES_RU if name_locale == 'uk' else NAME_ALIASES_UK
    name_hit = _first_alias_hit(normalized, name_aliases) or _first_alias_hit(
        normalized, fallback_name,
    )
    if name_hit:
        mapping['name'] = name_hit

    desc_aliases = (
        DESCRIPTION_ALIASES_UK if name_locale == 'uk' else DESCRIPTION_ALIASES_RU
    )
    fallback_desc = (
        DESCRIPTION_ALIASES_RU if name_locale == 'uk' else DESCRIPTION_ALIASES_UK
    )
    desc_hit = _first_alias_hit(normalized, desc_aliases) or _first_alias_hit(
        normalized, fallback_desc,
    )
    if desc_hit:
        mapping['description'] = desc_hit

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


def _map_rows(
    headers: list[str],
    raw_rows: list[Mapping[str, Any]],
    *,
    name_locale: NameLocale,
) -> list[dict[str, str]]:
    column_map = _build_column_map(headers, name_locale=name_locale)
    if 'sku' not in column_map:
        raise SupplierImportParseError(
            'Не знайдено колонку з артикулом. У файлі має бути колонка '
            '«Код_товара» (або sku / артикул). Перевірте перший рядок файлу.',
        )
    logger.info(
        'Supplier parse column_map=%s name_locale=%s',
        column_map,
        name_locale,
    )
    rows = _rows_from_mappings(raw_rows, column_map)
    if not rows:
        raise SupplierImportParseError(
            'У файлі немає рядків з товарами. Перевірте, що це повна вигрузка, '
            'а не лише заголовки.',
        )
    return rows


def parse_csv(
    file_obj: BinaryIO | io.TextIOBase,
    *,
    name_locale: NameLocale = 'uk',
) -> list[dict[str, str]]:
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
    raw_rows = [dict(row) for row in reader]
    return _map_rows(headers, raw_rows, name_locale=name_locale)


def parse_xlsx(
    file_obj: BinaryIO,
    *,
    name_locale: NameLocale = 'uk',
) -> list[dict[str, str]]:
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

        header_index = {h: i for i, h in enumerate(headers)}
        raw_rows: list[dict[str, Any]] = []
        for values in iterator:
            row_dict: dict[str, Any] = {}
            for header, idx in header_index.items():
                row_dict[header] = values[idx] if idx < len(values) else None
            raw_rows.append(row_dict)

        return _map_rows(headers, raw_rows, name_locale=name_locale)
    finally:
        workbook.close()


def parse_json(
    file_obj: BinaryIO | io.TextIOBase,
    *,
    name_locale: NameLocale = 'uk',
) -> list[dict[str, str]]:
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

    return _map_rows(headers, payload, name_locale=name_locale)


def parse_supplier_file(
    file_obj: BinaryIO,
    filename: str,
    *,
    name_locale: NameLocale = 'uk',
) -> list[dict[str, str]]:
    """Визначає формат за розширенням і парсить файл."""
    name = (filename or '').lower().strip()
    logger.info('Parsing supplier file name=%s locale=%s', name, name_locale)

    if name.endswith('.csv'):
        return parse_csv(file_obj, name_locale=name_locale)
    if name.endswith('.xlsx'):
        return parse_xlsx(file_obj, name_locale=name_locale)
    if name.endswith('.json'):
        return parse_json(file_obj, name_locale=name_locale)

    raise SupplierImportParseError(
        'Непідтримуваний формат файлу. Збережіть вигрузку як .xlsx, .csv або .json '
        'і спробуйте знову.',
    )
