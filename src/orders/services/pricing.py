"""Єдина логіка цін кошика / замовлення / LiqPay (товари без доставки)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Iterable

TWOPLACES = Decimal('0.01')


def quantize_money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PricingResult:
    lines: list[dict[str, Any]]
    subtotal: Decimal
    discount: Decimal
    total: Decimal


def _iter_raw_lines(lines_or_cart) -> Iterable[dict[str, Any]]:
    if hasattr(lines_or_cart, 'get_lines'):
        return lines_or_cart.get_lines()
    return lines_or_cart


def price_cart(lines_or_cart, promo=None) -> PricingResult:
    """
    Unit = Product.price; promo на subtotal; Decimal ROUND_HALF_UP до 0.01.
    ``total`` — сума товарів після знижки (без delivery_cost).
    """
    priced: list[dict[str, Any]] = []
    subtotal = Decimal('0.00')

    for row in _iter_raw_lines(lines_or_cart):
        product = row['product']
        quantity = int(row['quantity'])
        unit_price = quantize_money(product.price)
        line_total = quantize_money(unit_price * quantity)
        priced.append({
            'product': product,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total,
        })
        subtotal += line_total

    subtotal = quantize_money(subtotal)
    if promo is not None:
        discount = quantize_money(promo.discount_for(subtotal))
    else:
        discount = Decimal('0.00')
    discount = min(discount, subtotal)
    total = quantize_money(subtotal - discount)
    if total < 0:
        total = Decimal('0.00')
    return PricingResult(
        lines=priced,
        subtotal=subtotal,
        discount=discount,
        total=total,
    )
