"""Resend HTTP API client (https://resend.com/docs/api-reference/emails/send-email)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

API_SEND_URL = 'https://api.resend.com/emails'
REQUEST_TIMEOUT_DEFAULT = 10
# Cloudflare на api.resend.com блокує дефолтний User-Agent Python urllib (Error 1010).
RESEND_USER_AGENT = 'OyraResend/1.0 (+https://oyra.com.ua)'


class ResendError(Exception):
    pass


class ResendService:
    def __init__(
        self,
        api_key: str | None = None,
        timeout: int | None = None,
    ):
        self.api_key = api_key if api_key is not None else getattr(settings, 'RESEND_API_KEY', '')
        self.timeout = (
            timeout if timeout is not None
            else getattr(settings, 'RESEND_TIMEOUT', REQUEST_TIMEOUT_DEFAULT)
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def send(
        self,
        *,
        from_email: str,
        to: list[str],
        subject: str,
        text: str = '',
        html: str = '',
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self.configured:
            raise ResendError('Resend API key не заданий')

        recipients = [addr.strip() for addr in to if addr and addr.strip()]
        if not recipients:
            raise ResendError('Немає отримувачів email')

        from_email = (from_email or '').strip()
        if not from_email:
            raise ResendError('Не задано from_email')

        subject = (subject or '').strip()
        if not subject:
            raise ResendError('Порожня тема листа')

        payload: dict[str, Any] = {
            'from': from_email,
            'to': recipients,
            'subject': subject,
        }
        if text:
            payload['text'] = text
        if html:
            payload['html'] = html
        if cc:
            payload['cc'] = [addr.strip() for addr in cc if addr and addr.strip()]
        if bcc:
            payload['bcc'] = [addr.strip() for addr in bcc if addr and addr.strip()]
        if reply_to:
            payload['reply_to'] = [addr.strip() for addr in reply_to if addr and addr.strip()]

        if not text and not html:
            payload['text'] = ''

        logger.info(
            'Resend sending: from=%s to=%s subject=%r',
            from_email,
            recipients,
            subject[:80],
        )
        return self._post(payload)

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(
            API_SEND_URL,
            data=body,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
                'User-Agent': RESEND_USER_AGENT,
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
                'Resend HTTP error: status=%s body=%s',
                exc.code,
                error_body,
            )
            raise ResendError(f'Resend HTTP {exc.code}: {error_body}') from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            logger.warning('Resend request failed: %s', exc)
            raise ResendError('Помилка запиту до Resend API') from exc

        email_id = data.get('id')
        if not email_id:
            logger.warning('Resend unexpected response: %s', data)
            raise ResendError(f'Resend error: {data}')

        logger.info('Resend API success: id=%s', email_id)
        return {'ok': True, 'id': email_id, 'raw': data}
