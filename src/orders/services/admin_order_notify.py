"""Сповіщення адміністраторів про нове замовлення (email + TurboSMS Viber/SMS)."""
from __future__ import annotations

import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from src.core.models import SiteSettings
from src.orders.models import Order
from src.orders.services.turbosms import TurboSMSError, TurboSMSService

logger = logging.getLogger(__name__)
User = get_user_model()

_SPLIT_RE = re.compile(r'[,;\s]+')


def _split_contacts(raw: str) -> list[str]:
    return [part.strip() for part in _SPLIT_RE.split(raw or '') if part.strip()]


def build_admin_order_text(order: Order) -> str:
    payment = order.get_payment_method_display() if order.payment_method else '—'
    return (
        f'Oyra: нове замовлення {order.order_number}\n'
        f'{order.first_name} {order.last_name}, {order.phone}\n'
        f'Сума: {order.total} грн\n'
        f'Оплата: {payment}\n'
        f'Доставка: {order.get_delivery_service_display()} / {order.delivery_city}'
    )


def collect_admin_email_recipients(settings_obj: SiteSettings | None = None) -> list[str]:
    settings_obj = settings_obj or SiteSettings.get_solo()
    emails: set[str] = set()
    for item in _split_contacts(settings_obj.notify_emails):
        if '@' in item:
            emails.add(item.lower())
    staff = User.objects.filter(
        is_active=True,
        is_staff=True,
        notify_email=True,
    ).exclude(email='').values_list('email', flat=True)
    for email in staff:
        emails.add(email.lower())
    return sorted(emails)


def collect_admin_phone_recipients(settings_obj: SiteSettings | None = None) -> list[str]:
    settings_obj = settings_obj or SiteSettings.get_solo()
    phones: list[str] = []
    seen: set[str] = set()
    for item in _split_contacts(settings_obj.notify_phones):
        if item not in seen:
            seen.add(item)
            phones.append(item)
    staff = User.objects.filter(
        is_active=True,
        is_staff=True,
        notify_messenger=True,
    ).exclude(phone='').only('phone')
    for user in staff:
        phone = (user.phone or '').strip()
        if phone and phone not in seen:
            seen.add(phone)
            phones.append(phone)
    return phones


def notify_admins_new_order(order: Order) -> dict[str, int]:
    """
    Дублює сповіщення про нове замовлення на глобальні контакти та staff.
    Помилки каналів логуються, не переривають checkout.
    """
    result = {'email': 0, 'messenger': 0}
    text = build_admin_order_text(order)
    site = SiteSettings.get_solo()

    emails = collect_admin_email_recipients(site)
    if emails:
        subject = f'Нове замовлення {order.order_number}'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@oyra.ua')
        try:
            sent = send_mail(
                subject,
                text,
                from_email,
                emails,
                fail_silently=True,
            )
            result['email'] = int(sent or 0)
        except Exception:
            logger.exception('Admin order email failed for %s', order.order_number)

    phones = collect_admin_phone_recipients(site)
    if phones and getattr(settings, 'TURBOSMS_ENABLED', False):
        service = TurboSMSService()
        if service.can_send:
            for phone in phones:
                try:
                    if service.send(phone, text):
                        result['messenger'] += 1
                except TurboSMSError as exc:
                    logger.warning(
                        'Admin messenger notify failed for %s (%s): %s',
                        order.order_number,
                        phone,
                        exc,
                    )
                except Exception:
                    logger.exception(
                        'Admin messenger notify error for %s (%s)',
                        order.order_number,
                        phone,
                    )
    return result
