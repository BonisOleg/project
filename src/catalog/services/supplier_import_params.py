"""Характеристики з вигрузки Prom/Siker (дубльовані колонки + JSON params)."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

SKIP_ATTR_NAMES = frozenset({
    'артикул',
    'код товара',
    'код_товара',
    'sku',
    'vendorcode',
    'vendor_code',
})

_NAME_RU = frozenset({
    'название_характеристики',
    'назва_характеристики',
    'название характеристики',
    'назва характеристики',
    'param_name',
    'characteristic_name',
})
_NAME_UK = frozenset({
    'название_характеристики_укр',
    'назва_характеристики_укр',
    'название характеристики укр',
    'назва характеристики укр',
    'param_name_uk',
})
_VALUE_RU = frozenset({
    'значение_характеристики',
    'значення_характеристики',
    'значение характеристики',
    'значення характеристики',
    'param_value',
    'characteristic_value',
})
_VALUE_UK = frozenset({
    'значение_характеристики_укр',
    'значення_характеристики_укр',
    'значение характеристики укр',
    'значення характеристики укр',
    'param_value_uk',
})
_UNIT = frozenset({
    'измерение_характеристики',
    'вимірювання_характеристики',
    'измерение характеристики',
    'единица_измерения',
    'одиниця_вимірювання',
    'param_unit',
})


def _norm_header(raw: Any) -> str:
    text = str(raw or '').strip().lower().replace('\ufeff', '')
    text = ' '.join(text.replace('-', '_').split())
    return re.sub(r'_\d+$', '', text)


def _header_kind(header: Any) -> str | None:
    key = _norm_header(header)
    if not key:
        return None
    if key in _NAME_UK:
        return 'name_uk'
    if key in _NAME_RU:
        return 'name_ru'
    if key in _VALUE_UK:
        return 'value_uk'
    if key in _VALUE_RU:
        return 'value_ru'
    if key in _UNIT:
        return 'unit'
    return None


def _cell(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _combine_value(value: str, unit: str) -> str:
    if not unit:
        return value
    if not value:
        return unit
    if value.lower().endswith(unit.lower()):
        return value
    return f'{value} {unit}'.strip()


def _pick_locale(ru: str, uk: str, name_locale: str) -> str:
    if name_locale == 'uk':
        return uk or ru
    return ru or uk


def _flush_group(
    group: dict[str, str],
    name_locale: str,
    seen: set[str],
    out: list[tuple[str, str]],
) -> None:
    name = _pick_locale(group['name_ru'], group['name_uk'], name_locale)
    value = _pick_locale(group['value_ru'], group['value_uk'], name_locale)
    value = _combine_value(value, group['unit'])
    name = name[:120].strip()
    value = value[:255].strip()
    if not name or not value:
        return
    if name.lower() in SKIP_ATTR_NAMES:
        return
    key = name.lower()
    if key in seen:
        return
    seen.add(key)
    out.append((name, value))


def extract_prom_attributes(
    headers: Sequence[Any],
    values: Sequence[Any],
    *,
    name_locale: str = 'uk',
) -> list[tuple[str, str]]:
    """Збирає всі пари назва/значення з дубльованих колонок Prom."""
    empty = {
        'name_ru': '',
        'name_uk': '',
        'value_ru': '',
        'value_uk': '',
        'unit': '',
    }
    group = dict(empty)
    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    for index, header in enumerate(headers):
        kind = _header_kind(header)
        if kind is None:
            continue
        cell = _cell(values[index] if index < len(values) else '')
        if kind == 'name_ru' and any(group.values()):
            _flush_group(group, name_locale, seen, out)
            group = dict(empty)
        elif kind == 'name_uk' and group['name_uk']:
            _flush_group(group, name_locale, seen, out)
            group = dict(empty)
        group[kind] = cell

    if any(group.values()):
        _flush_group(group, name_locale, seen, out)
    return out


def extract_mapping_attributes(
    raw: Mapping[str, Any],
    *,
    name_locale: str = 'uk',
) -> list[tuple[str, str]]:
    """JSON: params/attributes + колонки Prom у ключах обʼєкта."""
    headers = list(raw.keys())
    values = [raw.get(key) for key in headers]
    out = extract_prom_attributes(headers, values, name_locale=name_locale)
    if out:
        return out

    payload = raw.get('params') or raw.get('attributes') or raw.get('характеристики')
    seen: set[str] = set()
    result: list[tuple[str, str]] = []

    if isinstance(payload, Mapping):
        for name, value in payload.items():
            _flush_group(
                {
                    'name_ru': _cell(name) if name_locale == 'ru' else '',
                    'name_uk': _cell(name) if name_locale == 'uk' else _cell(name),
                    'value_ru': _cell(value) if name_locale == 'ru' else '',
                    'value_uk': _cell(value) if name_locale == 'uk' else _cell(value),
                    'unit': '',
                },
                name_locale,
                seen,
                result,
            )
        return result

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, Mapping):
                continue
            name = _cell(item.get('name') or item.get('назва') or item.get('название'))
            value = _cell(item.get('value') or item.get('значення') or item.get('значение'))
            _flush_group(
                {
                    'name_ru': name,
                    'name_uk': name,
                    'value_ru': value,
                    'value_uk': value,
                    'unit': _cell(item.get('unit') or ''),
                },
                name_locale,
                seen,
                result,
            )
    return result


def sync_product_attributes(product, attributes: list[tuple[str, str]] | None) -> int:
    """Перезаписує характеристики, якщо у файлі був хоча б один param."""
    from src.catalog.models import ProductAttribute

    if not attributes:
        return 0
    product.attributes.all().delete()
    ProductAttribute.objects.bulk_create(
        [
            ProductAttribute(
                product=product,
                name=name,
                value=value,
                sort_order=index,
            )
            for index, (name, value) in enumerate(attributes)
        ],
    )
    return len(attributes)
