"""Валідатори публічних полів: імʼя, місто, телефон UA, довжина тексту."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError

_NAME_RE = re.compile(
    r"^[^\W\d_]+(?:[ '\u2019-][^\W\d_]+)*$",
    re.UNICODE,
)
_PHONE_DIGITS_RE = re.compile(r'\D+')
_PLACE_ALLOWED = set(" '\u2019.,()-")


def clean_person_name(value, *, required=True, label='Імʼя'):
    """2–100 символів: літери, пробіл, дефіс, апостроф."""
    text = (value or '').strip()
    if not text:
        if required:
            raise ValidationError(f'Вкажіть {label.lower()}.')
        return ''
    if not 2 <= len(text) <= 100:
        raise ValidationError(f'{label} має містити від 2 до 100 символів.')
    if _NAME_RE.fullmatch(text) is None:
        raise ValidationError(
            f'{label} може містити лише літери, пробіл, дефіс або апостроф.',
        )
    return text


def clean_place(value, *, max_len=150, label='Місто'):
    """Назва населеного пункту без цифр. Дозволяє кому, крапку й дужки (Нова Пошта)."""
    text = (value or '').strip()
    if not 2 <= len(text) <= max_len:
        raise ValidationError(f'{label} має містити від 2 до {max_len} символів.')
    for ch in text:
        if ch.isdigit() or ch == '_':
            raise ValidationError(f'{label} не може містити цифри.')
        if ch.isalpha() or ch in _PLACE_ALLOWED:
            continue
        raise ValidationError(f'{label} містить неприпустимий символ.')
    return text


def normalize_ua_phone(value, *, required=True):
    """Повертає +380XXXXXXXXX. Приймає 380…, 0… або 9 цифр абонента."""
    raw = (value or '').strip()
    if not raw:
        if required:
            raise ValidationError('Вкажіть номер телефону.')
        return ''
    if len(raw) > 32:
        raise ValidationError('Номер телефону занадто довгий.')
    digits = _PHONE_DIGITS_RE.sub('', raw)
    national = ''
    if digits.startswith('380') and len(digits) == 12:
        national = digits[3:]
    elif digits.startswith('0') and len(digits) == 10:
        national = digits[1:]
    elif len(digits) == 9:
        national = digits
    if len(national) != 9:
        raise ValidationError('Вкажіть український номер у форматі +380XXXXXXXXX.')
    return f'+380{national}'


def clean_limited_text(value, *, max_len, required=False, label='Поле'):
    text = (value or '').strip()
    if required and not text:
        raise ValidationError(f'Заповніть поле «{label}».')
    if len(text) > max_len:
        raise ValidationError(f'Максимум {max_len} символів.')
    if any(ord(ch) < 32 and ch not in '\n\r\t' for ch in text):
        raise ValidationError('Поле містить неприпустимі символи.')
    return text
