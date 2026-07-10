from django import template
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from src.core.block_defaults import BLOCK_DEFAULTS
from src.core.utils.block_render import get_block_text, is_section_visible, render_block_html

register = template.Library()


@register.simple_tag(takes_context=True)
def block_plain(context, page: str, key: str, fallback: str = '') -> str:
    blocks = context.get('site_blocks', {})
    settings = context.get('site_settings')
    return get_block_text(
        page,
        key,
        site_blocks=blocks,
        fallback=fallback,
        site_settings=settings,
    )


@register.simple_tag(takes_context=True)
def section_visible(context, page: str, visibility_key: str) -> bool:
    blocks = context.get('site_blocks', {})
    return is_section_visible(page, visibility_key, site_blocks=blocks)


@register.simple_tag(takes_context=True)
def block_image(
    context,
    page: str,
    key: str,
    css_class: str = '',
    fallback_static: str = '',
    width: int | None = None,
    height: int | None = None,
) -> str:
    blocks = context.get('site_blocks', {})
    block = blocks.get(f'{page}.{key}')
    alt_key = f'{key}_alt'
    alt = get_block_text(page, alt_key, site_blocks=blocks, site_settings=context.get('site_settings'))
    size_attrs = ''
    if width:
        size_attrs += f' width="{width}"'
    if height:
        size_attrs += f' height="{height}"'

    if block is not None and block.is_active and block.image:
        if css_class:
            return format_html(
                '<img class="{}" src="{}" alt="{}" loading="eager" decoding="async"{}/>',
                css_class,
                block.image.url,
                alt,
                mark_safe(size_attrs),
            )
        return format_html(
            '<img src="{}" alt="{}" loading="eager" decoding="async"{}/>',
            block.image.url,
            alt,
            mark_safe(size_attrs),
        )

    if fallback_static:
        src = static(fallback_static)
        if css_class:
            return format_html(
                '<img class="{}" src="{}" alt="{}" loading="eager" decoding="async"{}/>',
                css_class,
                src,
                alt or BLOCK_DEFAULTS.get((page, alt_key), ''),
                mark_safe(size_attrs),
            )
        return format_html(
            '<img src="{}" alt="{}" loading="eager" decoding="async"{}/>',
            src,
            alt or BLOCK_DEFAULTS.get((page, alt_key), ''),
            mark_safe(size_attrs),
        )
    return ''


@register.simple_tag(takes_context=True)
def render_block(context, page: str, key: str, fallback: str = '') -> str:
    blocks = context.get('site_blocks', {})
    block = blocks.get(f'{page}.{key}')
    rendered = render_block_html(block)
    if rendered:
        return rendered
    return get_block_text(
        page,
        key,
        site_blocks=blocks,
        fallback=fallback,
        site_settings=context.get('site_settings'),
    )
