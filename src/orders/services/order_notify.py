"""Сповіщення клієнта про статус замовлення через TurboSMS (SMS / Viber / hybrid)."""

from __future__ import annotations

import logging

from django.conf import settings

from src.orders.models import Order
from src.orders.services.turbosms import TurboSMSError, TurboSMSService

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    Order.STATUS_PENDING: (
        'Oyra: замовлення {number} прийнято. Сума {total} грн. Дякуємо!'
    ),
    Order.STATUS_AWAITING_PAYMENT: (
        'Oyra: замовлення {number} очікує оплату. Сума {total} грн.'
    ),
    Order.STATUS_PAID: (
        'Oyra: замовлення {number} оплачено. Сума {total} грн.'
    ),
    Order.STATUS_PROCESSING: (
        'Oyra: замовлення {number} в обробці.'
    ),
    Order.STATUS_SHIPPED: (
        'Oyra: замовлення {number} відправлено.{tracking}'
    ),
    Order.STATUS_DONE: (
        'Oyra: замовлення {number} виконано. Дякуємо за покупку!'
    ),
    Order.STATUS_CANCELLED: (
        'Oyra: замовлення {number} скасовано. З питань — телефонуйте в магазин.'
    ),
}


def build_order_status_text(order: Order, status: str | None = None) -> str | None:
    status = status or order.status
    template = STATUS_MESSAGES.get(status)
    if not template:
        return None
    tracking = ''
    if status == Order.STATUS_SHIPPED and order.tracking_number:
        tracking = f' ТТН: {order.tracking_number}.'
    return template.format(
        number=order.order_number,
        total=order.total,
        tracking=tracking,
    )


def notify_order_status(order: Order, status: str | None = None) -> bool:
    """
    Надсилає SMS/Viber про статус. Помилки API не пробрасуються назовні.
    Повертає True, якщо запит прийнято шлюзом.
    """
    if not getattr(settings, 'TURBOSMS_ENABLED', False):
        return False

    text = build_order_status_text(order, status=status)
    if not text:
        return False

    service = TurboSMSService()
    if not service.can_send:
        logger.info(
            'Order SMS skipped for %s: TurboSMS not ready',
            order.order_number,
        )
        return False

    try:
        service.send(order.phone, text)
    except TurboSMSError as exc:
        logger.warning(
            'Order SMS failed for %s: %s',
            order.order_number,
            exc,
        )
        return False
    except Exception:
        logger.exception('Order SMS unexpected error for %s', order.order_number)
        return False

    logger.info('Order SMS queued for %s status=%s', order.order_number, status or order.status)
    return True
