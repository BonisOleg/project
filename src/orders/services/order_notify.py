"""Сповіщення клієнта про замовлення: email (Resend) + SMS/Viber (TurboSMS)."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

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
        logger.info(
            'Order SMS skipped for %s: TURBOSMS_ENABLED=False',
            order.order_number,
        )
        return False

    text = build_order_status_text(order, status=status)
    if not text:
        return False

    service = TurboSMSService()
    if not service.can_send:
        logger.info(
            'Order SMS skipped for %s: TurboSMS not ready (token/sender missing)',
            order.order_number,
        )
        return False

    logger.info(
        'Order SMS sending: order=%s status=%s phone_tail=%s',
        order.order_number,
        status or order.status,
        (order.phone or '')[-4:],
    )
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


def build_client_order_email(order: Order) -> tuple[str, str]:
    lines = [
        f'{item.product_name} x{item.quantity} — {item.line_total} грн'
        for item in order.items.all()
    ]
    subject = f'Oyra: замовлення {order.order_number} прийнято'
    body = (
        f'Доброго дня, {order.first_name}!\n\n'
        f'Дякуємо за замовлення {order.order_number} на сайті Oyra.\n\n'
        + ('\n'.join(lines) + '\n\n' if lines else '')
        + f'Разом: {order.total} грн\n'
        f'Доставка: {order.get_delivery_service_display()} / {order.delivery_city}\n'
        f'Оплата: {order.get_payment_method_display()}\n\n'
        f'Ми звʼяжемось з вами за номером {order.phone} для підтвердження.'
    )
    return subject, body


def notify_client_new_order(order: Order) -> bool:
    """
    Надсилає клієнту email-підтвердження нового замовлення через Resend.
    Помилки не переривають checkout — лише логуються.
    """
    if not order.email:
        logger.info('Client order email skipped for %s: no email', order.order_number)
        return False

    subject, body = build_client_order_email(order)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@oyra.ua')
    logger.info(
        'Client order email sending: order=%s to=%s backend=%s',
        order.order_number,
        order.email,
        settings.EMAIL_BACKEND,
    )
    try:
        sent = send_mail(subject, body, from_email, [order.email], fail_silently=False)
    except Exception:
        logger.exception('Client order email failed for %s', order.order_number)
        return False

    if not sent:
        logger.warning('Client order email not accepted for %s (send_mail=0)', order.order_number)
        return False

    logger.info('Client order email sent for %s', order.order_number)
    return True
