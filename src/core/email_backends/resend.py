"""Django email backend через Resend HTTP API (порт 443, без SMTP)."""

from __future__ import annotations

import logging

from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage

from src.core.services.resend import ResendError, ResendService

logger = logging.getLogger(__name__)


def _extract_bodies(message: EmailMessage) -> tuple[str, str]:
    text = ''
    html = ''
    if message.content_subtype == 'html':
        html = message.body
    else:
        text = message.body
    for content, mimetype in getattr(message, 'alternatives', []):
        if mimetype == 'text/html':
            html = content
        elif mimetype == 'text/plain' and not text:
            text = content
    return text, html


class ResendEmailBackend(BaseEmailBackend):
    """Відправка через https://api.resend.com/emails."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        service = ResendService()
        if not service.configured:
            if self.fail_silently:
                logger.warning('Resend backend skipped: API key missing')
                return 0
            raise ResendError('Resend API key не заданий')

        sent_count = 0
        for message in email_messages:
            try:
                if self._send_message(service, message):
                    sent_count += 1
            except Exception:
                if not self.fail_silently:
                    raise
                logger.exception('Resend send failed silently')
        return sent_count

    def _send_message(self, service: ResendService, message: EmailMessage) -> bool:
        text, html = _extract_bodies(message)
        service.send(
            from_email=message.from_email,
            to=list(message.to),
            subject=message.subject,
            text=text,
            html=html,
            cc=list(message.cc),
            bcc=list(message.bcc),
            reply_to=list(message.reply_to),
        )
        return True
