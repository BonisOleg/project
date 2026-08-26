"""Форматування телефонів для tel: посилань."""

from __future__ import annotations

import re

_PHONE_DIGITS_RE = re.compile(r'\D+')


def phone_to_tel_uri(phone: str) -> str:
    """Повертає номер у форматі +380XXXXXXXXX для коректного набору на iOS/Android."""
    digits = _PHONE_DIGITS_RE.sub('', phone or '')
    if not digits:
        return ''
    if digits.startswith('380') and len(digits) >= 12:
        return f'+{digits}'
    if digits.startswith('0') and len(digits) == 10:
        return f'+38{digits}'
    if len(digits) == 9:
        return f'+380{digits}'
    if phone.strip().startswith('+'):
        return f'+{digits}'
    return digits
