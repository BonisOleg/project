from decimal import Decimal

from django.db import transaction

from src.orders.models import Order, OrderItem
from src.orders.services.pricing import price_cart


def sync_order_with_cart(order, cart, session) -> bool:
    """
    Перераховує PENDING/AWAITING_PAYMENT замовлення з поточного кошика і промокоду.
    Повертає False, якщо кошик порожній (оплату починати не можна).
    Оплачені/підтверджені замовлення не змінює.
    """
    if order.status not in (Order.STATUS_PENDING, Order.STATUS_AWAITING_PAYMENT):
        return True

    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status not in (Order.STATUS_PENDING, Order.STATUS_AWAITING_PAYMENT):
            return True

        promo_code = (session.get('promo_code') or '').strip()
        promo = cart.apply_promo(promo_code) if promo_code else None
        if promo_code and not promo:
            session.pop('promo_code', None)
            session.modified = True
            promo_code = ''

        pricing = price_cart(cart, promo)
        if not pricing.lines:
            return False

        order.items.all().delete()
        for line in pricing.lines:
            OrderItem.objects.create(
                order=order,
                product=line['product'],
                product_name=line['product'].name,
                product_sku=line['product'].sku,
                price=line['unit_price'],
                quantity=line['quantity'],
                line_total=line['line_total'],
            )

        delivery = order.delivery_cost or Decimal('0.00')
        order.subtotal = pricing.subtotal
        order.discount = pricing.discount
        order.promo_code = promo.code if promo else ''
        order.total = pricing.total + delivery
        order.save(update_fields=[
            'subtotal', 'discount', 'promo_code', 'total', 'updated_at',
        ])

    return True
