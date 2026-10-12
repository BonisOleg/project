from decimal import Decimal

from django.db import transaction

from src.orders.models import Order, OrderItem


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

        lines = cart.get_lines()
        if not lines:
            return False

        order.items.all().delete()
        subtotal = Decimal('0')
        for line in lines:
            line_total = line['line_total']
            subtotal += line_total
            OrderItem.objects.create(
                order=order,
                product=line['product'],
                product_name=line['product'].name,
                product_sku=line['product'].sku,
                price=line['product'].price,
                quantity=line['quantity'],
                line_total=line_total,
            )

        promo_code = (session.get('promo_code') or '').strip()
        promo = cart.apply_promo(promo_code) if promo_code else None
        if promo_code and not promo:
            session.pop('promo_code', None)
            session.modified = True
            promo_code = ''

        if promo:
            goods_total = promo.apply_discount(subtotal)
            discount = subtotal - goods_total
            promo_code = promo.code
        else:
            goods_total = subtotal
            discount = Decimal('0')
            promo_code = ''

        order.subtotal = subtotal
        order.discount = discount
        order.promo_code = promo_code
        order.total = goods_total + (order.delivery_cost or Decimal('0'))
        order.save(update_fields=[
            'subtotal', 'discount', 'promo_code', 'total', 'updated_at',
        ])

    return True
