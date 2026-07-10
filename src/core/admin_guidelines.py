"""
Рекомендації для адмінки Oyra: ліміти зображень та символів.
Використовується у admin.py та admin_site_content.py для підказок користувачу.
"""
from __future__ import annotations

from typing import TypedDict


class ImageProfile(TypedDict):
    label: str
    recommended: str
    max_size_mb: int
    hint: str


IMAGE_PROFILES: dict[str, ImageProfile] = {
    'hero': {
        'label': 'Слайд hero-банера',
        'recommended': '1920×1080 пікселів',
        'max_size_mb': 3,
        'hint': (
            'JPG, PNG або WebP. Рекомендований розмір: 1920×1080 пікселів. '
            'Макс. 3 МБ. Файл буде автоматично конвертовано у WebP.'
        ),
    },
    'category': {
        'label': 'Фото категорії',
        'recommended': '800×800 пікселів',
        'max_size_mb': 1,
        'hint': 'JPG, PNG або WebP. Рекомендований розмір: 800×800 пікселів (квадрат). Макс. 1 МБ.',
    },
    'product': {
        'label': 'Фото товару',
        'recommended': '800×800 пікселів',
        'max_size_mb': 2,
        'hint': 'JPG, PNG або WebP. Рекомендований розмір: 800×800 пікселів. Макс. 2 МБ. Файл буде автоматично конвертовано у WebP.',
    },
    'blog': {
        'label': 'Фото для статті',
        'recommended': '1200×630 пікселів',
        'max_size_mb': 2,
        'hint': 'JPG, PNG або WebP. Рекомендований розмір: 1200×630 пікселів. Макс. 2 МБ. Файл буде автоматично конвертовано у WebP.',
    },
    'block_image': {
        'label': 'Зображення блоку',
        'recommended': '1200×800 пікселів',
        'max_size_mb': 2,
        'hint': 'JPG, PNG або WebP. Рекомендований розмір: 1200×800 пікселів. Макс. 2 МБ. Файл буде автоматично конвертовано у WebP.',
    },
}


TEXT_LIMITS: dict[str, int] = {
    'hero_eyebrow': 60,
    'hero_title': 100,
    'hero_lead': 220,
    'hero_btn_catalog': 30,
    'hero_btn_sale': 30,
    'products_section_title': 80,
    'categories_section_title': 80,
    'benefits_section_title': 80,
    'benefit_1_title': 60,
    'benefit_1_text': 130,
    'benefit_2_title': 60,
    'benefit_2_text': 130,
    'benefit_3_title': 60,
    'benefit_3_text': 130,
    'benefit_4_title': 60,
    'benefit_4_text': 130,
    'about_section_title': 100,
    'about_section_lead': 280,
    'blog_section_title': 80,
    'header_search_placeholder': 50,
    'header_nav_catalog_label': 30,
    'header_nav_sale_label': 30,
    'header_nav_news_label': 30,
    'footer_about_text': 280,
    'footer_copyright': 100,
    'footer_schedule': 80,
}


def get_image_hint(profile_key: str) -> str:
    """Повертає текст підказки для ImageField за профілем."""
    profile = IMAGE_PROFILES.get(profile_key)
    if profile:
        return profile['hint']
    return 'JPG, PNG або WebP. Файл буде автоматично конвертовано у WebP.'


def get_text_limit_hint(key: str) -> str | None:
    """Повертає підказку з лімітом символів для текстового поля."""
    limit = TEXT_LIMITS.get(key)
    if limit:
        return f'Рекомендована кількість символів: до {limit}.'
    return None
