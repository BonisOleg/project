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
    eligible_subtotal: Decimal = Decimal('0.00')
    sale_lines_count: int = 0

    @property
    def promo_excludes_sale_items(self) -> bool:
        return self.sale_lines_count > 0


def _iter_raw_lines(lines_or_cart) -> Iterable[dict[str, Any]]:
    if hasattr(lines_or_cart, 'get_lines'):
        return lines_or_cart.get_lines()
    return lines_or_cart


def is_on_sale(product) -> bool:
    """Те саме правило, що й на вітрині: old_price задана і вища за поточну ціну."""
    old_price = getattr(product, 'old_price', None)
    return bool(old_price) and Decimal(old_price) > Decimal(product.price)


def price_cart(lines_or_cart, promo=None) -> PricingResult:
    """
    Unit = Product.price; промокод діє лише на позиції НЕ на акції (is_on_sale),
    знижка рахується від їхньої суми і не перевищує її; Decimal ROUND_HALF_UP до 0.01.
    ``total`` — сума товарів після знижки (без delivery_cost).
    """
    priced: list[dict[str, Any]] = []
    subtotal = Decimal('0.00')
    eligible_subtotal = Decimal('0.00')
    sale_lines_count = 0

    for row in _iter_raw_lines(lines_or_cart):
        product = row['product']
        quantity = int(row['quantity'])
        unit_price = quantize_money(product.price)
        line_total = quantize_money(unit_price * quantity)
        on_sale = is_on_sale(product)
        if on_sale:
            sale_lines_count += 1
        else:
            eligible_subtotal += line_total
        priced.append({
            'product': product,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total,
            'on_sale': on_sale,
            'promo_eligible': not on_sale,
        })
        subtotal += line_total

    subtotal = quantize_money(subtotal)
    eligible_subtotal = quantize_money(eligible_subtotal)
    if promo is not None and eligible_subtotal > 0:
        discount = quantize_money(promo.discount_for(eligible_subtotal))
    else:
        discount = Decimal('0.00')
    discount = min(discount, eligible_subtotal)
    total = quantize_money(subtotal - discount)
    if total < 0:
        total = Decimal('0.00')
    return PricingResult(
        lines=priced,
        subtotal=subtotal,
        discount=discount,
        total=total,
        eligible_subtotal=eligible_subtotal,
        sale_lines_count=sale_lines_count,
    )
