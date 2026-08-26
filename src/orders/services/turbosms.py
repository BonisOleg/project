"""TurboSMS HTTP API client (SMS + Viber / hybrid).

Документація: https://turbosms.ua/ua/api.html
Каркас: достатньо заповнити TURBOSMS_* у .env.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

API_SEND_URL = 'https://api.turbosms.ua/message/send.json'
REQUEST_TIMEOUT_DEFAULT = 8

_PHONE_DIGITS_RE = re.compile(r'\D+')


class TurboSMSError(Exception):
    pass


def _looks_like_balance_error(data: dict[str, Any]) -> bool:
    """Евристика для швидкої діагностики: недостатньо коштів на балансі TurboSMS."""
    text = f"{data.get('response_status') or ''} {data.get('response_result') or ''}".lower()
    return any(word in text for word in ('balance', 'баланс', 'insufficient', 'кошт'))


def normalize_ua_phone(phone: str) -> str | None:
    """Повертає 380XXXXXXXXX або None, якщо номер невалідний."""
    digits = _PHONE_DIGITS_RE.sub('', phone or '')
    if digits.startswith('380') and len(digits) == 12:
        return digits
    if digits.startswith('0') and len(digits) == 10:
        return f'380{digits[1:]}'
    if len(digits) == 9:
        return f'380{digits}'
    if digits.startswith('38') and len(digits) == 12:
        return digits
    return None


class TurboSMSService:
    def __init__(
        self,
        token: str | None = None,
        sms_sender: str | None = None,
        viber_sender: str | None = None,
        enabled: bool | None = None,
        timeout: int | None = None,
        viber_ttl: int | None = None,
    ):
        self.token = token if token is not None else getattr(settings, 'TURBOSMS_TOKEN', '')
        self.sms_sender = (
            sms_sender if sms_sender is not None
            else getattr(settings, 'TURBOSMS_SMS_SENDER', '')
        )
        self.viber_sender = (
            viber_sender if viber_sender is not None
            else getattr(settings, 'TURBOSMS_VIBER_SENDER', '')
        )
        self.enabled = (
            enabled if enabled is not None
            else getattr(settings, 'TURBOSMS_ENABLED', False)
        )
        self.timeout = (
            timeout if timeout is not None
            else getattr(settings, 'TURBOSMS_TIMEOUT', REQUEST_TIMEOUT_DEFAULT)
        )
        self.viber_ttl = (
            viber_ttl if viber_ttl is not None
            else getattr(settings, 'TURBOSMS_VIBER_TTL', 3600)
        )

    @property
    def configured(self) -> bool:
        return bool(self.token) and (bool(self.sms_sender) or bool(self.viber_sender))

    @property
    def can_send(self) -> bool:
        return bool(self.enabled) and self.configured

    def send(
        self,
        phone: str,
        text: str,
        *,
        use_sms: bool | None = None,
        use_viber: bool | None = None,
    ) -> dict[str, Any]:
        """
        Надсилає повідомлення.

        Hybrid: якщо є обидва sender — SMS+Viber.
        Якщо лише один — тільки він.
        use_sms / use_viber дозволяють примусово обмежити канали.
        """
        if not self.can_send:
            logger.info('TurboSMS skipped: disabled or not configured')
            return {'skipped': True, 'reason': 'disabled_or_unconfigured'}

        recipient = normalize_ua_phone(phone)
        if not recipient:
            raise TurboSMSError('Невалідний номер телефону')

        text = (text or '').strip()
        if not text:
            raise TurboSMSError('Порожній текст повідомлення')

        send_sms = bool(self.sms_sender) if use_sms is None else bool(use_sms and self.sms_sender)
        send_viber = (
            bool(self.viber_sender) if use_viber is None
            else bool(use_viber and self.viber_sender)
        )
        if not send_sms and not send_viber:
            raise TurboSMSError('Немає активного каналу (SMS/Viber sender)')

        sms_block = {'sender': self.sms_sender, 'text': text} if send_sms else None
        viber_block = (
            {'sender': self.viber_sender, 'text': text, 'ttl': int(self.viber_ttl)}
            if send_viber else None
        )

        payload: dict[str, Any] = {'recipients': [recipient]}
        if sms_block:
            payload['sms'] = sms_block
        if viber_block:
            payload['viber'] = viber_block

        logger.info(
            'TurboSMS sending: recipient_tail=%s channels=%s',
            recipient[-4:],
            [c for c, b in (('sms', sms_block), ('viber', viber_block)) if b],
        )

        try:
            return self._post(payload)
        except TurboSMSError:
            # Viber-відправник ще не пройшов модерацію (або тимчасово недоступний) —
            # SMS не повинен постраждати через це, тому пробуємо ще раз лише SMS-каналом.
            if sms_block and viber_block:
                logger.warning(
                    'TurboSMS hybrid send failed for %s, retrying SMS-only',
                    recipient[-4:],
                )
                return self._post({'recipients': [recipient], 'sms': sms_block})
            raise

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(
            API_SEND_URL,
            data=body,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode('utf-8')
                data = json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode('utf-8', errors='replace') if exc.fp else ''
            logger.warning(
                'TurboSMS HTTP error: status=%s body=%s', exc.code, error_body,
            )
            raise TurboSMSError(f'TurboSMS HTTP {exc.code}: {error_body}') from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            logger.warning('TurboSMS request failed: %s', exc)
            raise TurboSMSError('Помилка запиту до TurboSMS') from exc

        if not self._is_success(data):
            logger.warning(
                'TurboSMS API error response: status=%s code=%s balance_issue=%s raw=%s',
                data.get('response_status'),
                data.get('response_code'),
                _looks_like_balance_error(data),
                data,
            )
            raise TurboSMSError(
                f"TurboSMS error: {data.get('response_status') or data.get('response_code')}"
            )

        logger.info(
            'TurboSMS API success: status=%s code=%s',
            data.get('response_status'),
            data.get('response_code'),
        )
        return {
            'ok': True,
            'raw': data,
            'result': data.get('response_result') or data.get('result') or data,
        }

    @staticmethod
    def _is_success(data: dict[str, Any]) -> bool:
        status = str(data.get('response_status') or '').upper()
        if status.startswith('SUCCESS') or status == 'OK':
            return True
        code = data.get('response_code')
        try:
            code_int = int(code)
        except (TypeError, ValueError):
            return False
        # 0 — OK; 8xx — SUCCESS_* (напр. 802 partial accepted)
        return code_int == 0 or 800 <= code_int < 900
