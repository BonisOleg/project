"""GA4 / GTM purchase payload для thank-you (Enhanced Conversions)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.orders.models import Order
from src.orders.services.turbosms import normalize_ua_phone


def _money_number(amount: Decimal | None) -> float:
    value = amount if amount is not None else Decimal('0')
    return float(value.quantize(Decimal('0.01')))


def _e164_ua_phone(raw: str) -> str | None:
    digits = normalize_ua_phone(raw)
    if not digits:
        return None
    return f'+{digits}'


def build_purchase_datalayer(order: Order) -> dict[str, Any]:
    """
    Payload для dataLayer.push на сторінці thank-you.

    Формат: event=purchase + ecommerce + user_data (Enhanced Conversions).
    """
    items: list[dict[str, Any]] = []
    for line in order.items.all():
        items.append({
            'item_id': line.product_sku,
            'item_name': line.product_name,
            'price': _money_number(line.price),
            'quantity': int(line.quantity),
        })

    user_data: dict[str, Any] = {
        'email': (order.email or '').strip().lower(),
        'address': {
            'first_name': (order.first_name or '').strip(),
            'last_name': (order.last_name or '').strip(),
            'street': (order.delivery_address or '').strip(),
            'city': (order.delivery_city or '').strip(),
            'country': 'UA',
        },
    }
    phone = _e164_ua_phone(order.phone or '')
    if phone:
        user_data['phone_number'] = phone

    return {
        'event': 'purchase',
        'ecommerce': {
            'transaction_id': order.order_number,
            'value': _money_number(order.total),
            'currency': 'UAH',
            'items': items,
        },
        'user_data': user_data,
    }
