"""Мітки Google Merchant: ціна, сезон, пріоритет, MPN генератора."""

from __future__ import annotations

import re
from decimal import Decimal

from src.catalog.models import Category, Product

LABEL_UNDER_800 = 'до 799'
LABEL_800 = '800-1999'
LABEL_2000 = '2000-4999'
LABEL_5000 = '5000+'

SEASON_WINTER = 'Зима'
SEASON_SPRING = 'Весна-літо'
SEASON_ALL = 'Всесезон'

PRIORITY_GENERATORS = 'Генератори'
PRIORITY_HIT = 'Хіт'
PRIORITY_STANDARD = 'Стандарт'

GENERATOR_CATEGORY_NAME = 'Генератори'

_PRICE_800 = Decimal('800')
_PRICE_2000 = Decimal('2000')
_PRICE_5000 = Decimal('5000')
_MPN_RE = re.compile(r'\b[A-Z]{2,}[A-Z0-9]*-\d+[A-Z0-9]*\b')

_SEASON_LABELS = {
    Category.FEED_SEASON_WINTER: SEASON_WINTER,
    Category.FEED_SEASON_SPRING: SEASON_SPRING,
    Category.FEED_SEASON_ALL: SEASON_ALL,
}


def load_categories() -> dict[int, Category]:
    rows = Category.objects.only('id', 'name', 'parent_id', 'feed_season')
    return {row.id: row for row in rows}


def feed_selling_price(product: Product) -> Decimal:
    """Та сама ціна, яку фід пише покупцю: sale_price, якщо є, інакше price."""
    price = product.price if product.price is not None else Decimal('0')
    old = product.old_price
    if old is not None and old > price:
        return price
    return price


def price_group(amount: Decimal) -> str:
    value = amount if isinstance(amount, Decimal) else Decimal(amount)
    if value < _PRICE_800:
        return LABEL_UNDER_800
    if value < _PRICE_2000:
        return LABEL_800
    if value < _PRICE_5000:
        return LABEL_2000
    return LABEL_5000


def _walk(category_id: int | None, by_id: dict[int, Category]):
    node = by_id.get(category_id) if category_id else None
    seen: set[int] = set()
    while node is not None and node.pk not in seen:
        seen.add(node.pk)
        yield node
        node = by_id.get(node.parent_id) if node.parent_id else None


def in_generators(category_id: int | None, by_id: dict[int, Category]) -> bool:
    for node in _walk(category_id, by_id):
        if (node.name or '').strip() == GENERATOR_CATEGORY_NAME:
            return True
    return False


def season_label(product: Product, by_id: dict[int, Category]) -> str:
    code = ''
    for node in _walk(product.category_id, by_id):
        code = (node.feed_season or '').strip()
        if code:
            break
    label = _SEASON_LABELS.get(code, SEASON_ALL)
    if label == SEASON_ALL and 'батут' in (product.name or '').casefold():
        return SEASON_SPRING
    return label


def priority_label(product: Product, by_id: dict[int, Category]) -> str:
    manual = {
        Product.FEED_PRIORITY_GENERATORS: PRIORITY_GENERATORS,
        Product.FEED_PRIORITY_HIT: PRIORITY_HIT,
        Product.FEED_PRIORITY_STANDARD: PRIORITY_STANDARD,
    }
    chosen = manual.get((product.feed_priority or '').strip())
    if chosen:
        return chosen
    if in_generators(product.category_id, by_id):
        return PRIORITY_GENERATORS
    if product.is_top_sale:
        return PRIORITY_HIT
    return PRIORITY_STANDARD


def generator_mpn(product: Product, by_id: dict[int, Category]) -> str | None:
    """Один код моделі в назві генератора з брендом. Інакше нічого не вигадувати."""
    if not in_generators(product.category_id, by_id):
        return None
    brand = product.brand if product.brand_id else None
    if brand is None or not (brand.name or '').strip():
        return None
    found = list(dict.fromkeys(_MPN_RE.findall(product.name or '')))
    if len(found) != 1:
        return None
    return found[0]
