from __future__ import annotations

from django.utils.html import format_html
from django.utils.safestring import mark_safe

from src.core.block_defaults import BLOCK_DEFAULTS


def apply_block_placeholders(text: str, site_settings=None) -> str:
    if '{discount}' in text and site_settings is not None:
        text = text.replace('{discount}', str(site_settings.newsletter_discount))
    return text


def get_block_text(
    page: str,
    key: str,
    site_blocks: dict | None = None,
    fallback: str = '',
    site_settings=None,
) -> str:
    blocks = site_blocks or {}
    block = blocks.get(f'{page}.{key}')
    if block is not None and block.is_active and block.text_html.strip():
        value = block.text_html.strip()
    else:
        value = (fallback or BLOCK_DEFAULTS.get((page, key), '')).strip()
    return apply_block_placeholders(value, site_settings=site_settings)


def is_section_visible(page: str, visibility_key: str, site_blocks: dict | None = None) -> bool:
    value = get_block_text(page, visibility_key, site_blocks=site_blocks, fallback='1')
    return value not in {'0', 'false', 'False', ''}


def render_block_html(block) -> str:
    if block is None or not block.is_active:
        return ''

    if block.content_type == block.ContentType.TEXT:
        return mark_safe(block.text_html)

    if block.content_type == block.ContentType.IMAGE and block.image:
        return format_html(
            '<img class="site-block-image" src="{}" alt="{}" loading="lazy" decoding="async">',
            block.image.url,
            block.label or '',
        )

    return ''
