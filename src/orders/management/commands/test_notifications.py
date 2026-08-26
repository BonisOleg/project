"""Ізольована перевірка Email (Resend) та SMS (TurboSMS) без оформлення замовлення.

Приклади:
    python3 manage.py test_notifications --email you@example.com
    python3 manage.py test_notifications --phone +380501112233
    python3 manage.py test_notifications --email you@example.com --phone +380501112233
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandParser

from src.orders.services.turbosms import TurboSMSError, TurboSMSService


class Command(BaseCommand):
    help = 'Ізольована перевірка відправки Email (Resend) та SMS (TurboSMS).'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--email', help='Email для тестового листа')
        parser.add_argument('--phone', help='Телефон для тестового SMS (+380... або 0...)')

    def handle(self, *args, **options) -> None:
        email = options.get('email')
        phone = options.get('phone')
        if not email and not phone:
            self.stderr.write(self.style.ERROR(
                'Вкажіть --email та/або --phone. Приклад:\n'
                'python3 manage.py test_notifications '
                '--email you@example.com --phone +380501112233',
            ))
            return
        if email:
            self._test_email(email)
        if phone:
            self._test_sms(phone)

    def _test_email(self, email: str) -> None:
        self.stdout.write('--- EMAIL (Resend HTTP API) ---')
        self.stdout.write(f'EMAIL_BACKEND    = {settings.EMAIL_BACKEND}')
        self.stdout.write(
            f'RESEND_API_KEY задано = {bool(getattr(settings, "RESEND_API_KEY", ""))}',
        )
        self.stdout.write(f'DEFAULT_FROM_EMAIL = {settings.DEFAULT_FROM_EMAIL}')

        if settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
            self.stdout.write(self.style.WARNING(
                'EMAIL_BACKEND = console -> лист буде лише виведений у консоль, '
                'реально НЕ надійде. Додайте RESEND_API_KEY (або EMAIL_HOST_PASSWORD=re_...) '
                'у .env і перезапустіть.',
            ))

        try:
            sent = send_mail(
                'Oyra: тестовий лист',
                'Це тестове повідомлення для перевірки Resend HTTP API.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception as exc:  # noqa: BLE001 — навмисно ловимо все для діагностики
            self.stdout.write(self.style.ERROR(f'ПОМИЛКА при відправці email: {exc!r}'))
            return

        if sent:
            self.stdout.write(self.style.SUCCESS(f'OK: лист прийнято для {email}'))
        else:
            self.stdout.write(self.style.ERROR('send_mail() повернув 0 — лист не надіслано'))

    def _test_sms(self, phone: str) -> None:
        self.stdout.write('--- SMS (TurboSMS) ---')
        self.stdout.write(f'TURBOSMS_ENABLED     = {getattr(settings, "TURBOSMS_ENABLED", False)}')
        self.stdout.write(
            f'TURBOSMS_SMS_SENDER   = {getattr(settings, "TURBOSMS_SMS_SENDER", "")!r}',
        )
        self.stdout.write(
            f'TURBOSMS_VIBER_SENDER = {getattr(settings, "TURBOSMS_VIBER_SENDER", "")!r}',
        )
        self.stdout.write(
            f'TURBOSMS_TOKEN задано = {bool(getattr(settings, "TURBOSMS_TOKEN", ""))}',
        )

        service = TurboSMSService()
        if not service.can_send:
            self.stdout.write(self.style.ERROR(
                'can_send = False -> перевірте TURBOSMS_ENABLED, TURBOSMS_TOKEN, '
                'TURBOSMS_SMS_SENDER у .env',
            ))
            return

        try:
            result = service.send(phone, 'Oyra: тестове SMS-повідомлення.')
        except TurboSMSError as exc:
            self.stdout.write(self.style.ERROR(f'TurboSMSError: {exc}'))
            return
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(f'Неочікувана помилка: {exc!r}'))
            return

        self.stdout.write(self.style.SUCCESS(f'OK: {result}'))
