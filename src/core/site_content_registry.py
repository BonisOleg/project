from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from django.urls import reverse_lazy

from src.core.block_defaults import BLOCK_FIELD_LABELS


@dataclass(frozen=True)
class FieldGroup:
    title: str
    block_keys: tuple[str, ...]


@dataclass(frozen=True)
class ContentSection:
    slug: str
    page_slug: str
    title: str
    blocks: tuple[tuple[str, str], ...]
    sidebar_title: str = ''
    sidebar_icon: str = 'edit_note'
    preview_url: str = '/'
    description: str = ''
    visibility_key: str = ''
    field_groups: tuple[FieldGroup, ...] = field(default_factory=tuple)
    admin_model_name: str = ''


CONTENT_SECTIONS: tuple[ContentSection, ...] = (
    ContentSection(
        slug='hero',
        page_slug='home',
        title='Головний банер',
        sidebar_title='Головна — Hero',
        sidebar_icon='image',
        preview_url='/',
        admin_model_name='homeherosettings',
        description='Заголовок, текст, кнопки та фото hero-блоку.',
        visibility_key='hero_section_visible',
        blocks=(
            ('home', 'hero_eyebrow'),
            ('home', 'hero_title'),
            ('home', 'hero_lead'),
            ('home', 'hero_image'),
            ('home', 'hero_image_alt'),
            ('home', 'hero_btn_catalog'),
            ('home', 'hero_btn_sale'),
        ),
        field_groups=(
            FieldGroup('Мітка і заголовок', ('hero_eyebrow', 'hero_title', 'hero_lead')),
            FieldGroup('Зображення', ('hero_image', 'hero_image_alt')),
            FieldGroup('Кнопки', ('hero_btn_catalog', 'hero_btn_sale')),
        ),
    ),
    ContentSection(
        slug='products',
        page_slug='home',
        title='Популярні товари',
        sidebar_title='Головна — Товари',
        sidebar_icon='inventory_2',
        preview_url='/#products',
        admin_model_name='homeproductssettings',
        visibility_key='products_section_visible',
        description='Заголовок секції. Товари керуються в каталозі.',
        blocks=(('home', 'products_section_title'),),
        field_groups=(FieldGroup('Заголовок секції', ('products_section_title',)),),
    ),
    ContentSection(
        slug='categories',
        page_slug='home',
        title='Популярні категорії',
        sidebar_title='Головна — Категорії',
        sidebar_icon='category',
        preview_url='/#categories',
        admin_model_name='homecategoriessettings',
        visibility_key='categories_section_visible',
        description='Заголовок секції. Категорії керуються в каталозі.',
        blocks=(('home', 'categories_section_title'),),
        field_groups=(FieldGroup('Заголовок секції', ('categories_section_title',)),),
    ),
    ContentSection(
        slug='benefits',
        page_slug='home',
        title='Наші переваги',
        sidebar_title='Головна — Переваги',
        sidebar_icon='star',
        preview_url='/#benefits',
        admin_model_name='homebenefitssettings',
        visibility_key='benefits_section_visible',
        blocks=(
            ('home', 'benefits_section_title'),
            ('home', 'benefit_1_title'),
            ('home', 'benefit_1_text'),
            ('home', 'benefit_2_title'),
            ('home', 'benefit_2_text'),
            ('home', 'benefit_3_title'),
            ('home', 'benefit_3_text'),
            ('home', 'benefit_4_title'),
            ('home', 'benefit_4_text'),
        ),
        field_groups=(
            FieldGroup('Заголовок секції', ('benefits_section_title',)),
            FieldGroup('Перевага 1', ('benefit_1_title', 'benefit_1_text')),
            FieldGroup('Перевага 2', ('benefit_2_title', 'benefit_2_text')),
            FieldGroup('Перевага 3', ('benefit_3_title', 'benefit_3_text')),
            FieldGroup('Перевага 4', ('benefit_4_title', 'benefit_4_text')),
        ),
    ),
    ContentSection(
        slug='about',
        page_slug='home',
        title='Про магазин',
        sidebar_title='Головна — Про нас',
        sidebar_icon='store',
        preview_url='/#about',
        admin_model_name='homeaboutsettings',
        visibility_key='about_section_visible',
        blocks=(
            ('home', 'about_section_title'),
            ('home', 'about_section_lead'),
        ),
        field_groups=(
            FieldGroup('Текст секції', ('about_section_title', 'about_section_lead')),
        ),
    ),
    ContentSection(
        slug='blog',
        page_slug='home',
        title='Блог',
        sidebar_title='Головна — Блог',
        sidebar_icon='newspaper',
        preview_url='/#blog',
        admin_model_name='homeblogsettings',
        visibility_key='blog_section_visible',
        description='Заголовок секції. Статті керуються в розділі «Блог».',
        blocks=(('home', 'blog_section_title'),),
        field_groups=(FieldGroup('Заголовок секції', ('blog_section_title',)),),
    ),
    ContentSection(
        slug='header',
        page_slug='site',
        title='Верхнє меню та навігація',
        sidebar_title='Меню навігації',
        sidebar_icon='web',
        preview_url='/',
        admin_model_name='siteheadersettings',
        description='Підписи пунктів меню та їх видимість у верхньому та мобільному меню.',
        blocks=(
            ('site', 'header_search_placeholder'),
            ('site', 'header_search_visible'),
            ('site', 'header_nav_catalog_label'),
            ('site', 'header_nav_catalog_visible'),
            ('site', 'header_nav_sale_label'),
            ('site', 'header_nav_sale_visible'),
            ('site', 'header_nav_news_label'),
            ('site', 'header_nav_news_visible'),
            ('site', 'header_action_phone_visible'),
            ('site', 'header_action_wishlist_visible'),
            ('site', 'header_action_compare_visible'),
            ('site', 'header_action_cart_visible'),
            ('site', 'header_action_login_visible'),
            ('site', 'header_nav_delivery_visible'),
            ('site', 'header_nav_about_visible'),
        ),
        field_groups=(
            FieldGroup('Пошук', ('header_search_placeholder', 'header_search_visible')),
            FieldGroup('Каталог', ('header_nav_catalog_label', 'header_nav_catalog_visible')),
            FieldGroup('Акції', ('header_nav_sale_label', 'header_nav_sale_visible')),
            FieldGroup('Новини', ('header_nav_news_label', 'header_nav_news_visible')),
            FieldGroup('Іконки шапки', (
                'header_action_phone_visible',
                'header_action_wishlist_visible',
                'header_action_compare_visible',
                'header_action_cart_visible',
                'header_action_login_visible',
            )),
            FieldGroup('Мобільне меню', (
                'header_nav_delivery_visible',
                'header_nav_about_visible',
            )),
        ),
    ),
    ContentSection(
        slug='footer',
        page_slug='site',
        title='Нижній блок сайту',
        sidebar_title='Нижній блок',
        sidebar_icon='footer',
        preview_url='/',
        admin_model_name='sitefootersettings',
        description='Текст з описом магазину, копірайт та графік роботи у нижній частині сайту.',
        blocks=(
            ('site', 'footer_about_text'),
            ('site', 'footer_copyright'),
            ('site', 'footer_schedule'),
        ),
        field_groups=(
            FieldGroup('Опис магазину', ('footer_about_text',)),
            FieldGroup('Контактна інформація', ('footer_copyright', 'footer_schedule')),
        ),
    ),
)

SECTION_BY_ADMIN_MODEL = {section.admin_model_name: section for section in CONTENT_SECTIONS}


def get_block_field_label(page: str, key: str) -> str:
    return BLOCK_FIELD_LABELS.get((page, key), key.replace('_', ' ').capitalize())


def get_section(page_slug: str, section_slug: str) -> ContentSection:
    for section in CONTENT_SECTIONS:
        if section.page_slug == page_slug and section.slug == section_slug:
            return section
    raise KeyError(f'Section {section_slug!r} not found on page {page_slug!r}')


def get_section_by_admin_model(admin_model_name: str) -> ContentSection:
    try:
        return SECTION_BY_ADMIN_MODEL[admin_model_name]
    except KeyError as exc:
        raise KeyError(f'Section for admin model {admin_model_name!r} not found') from exc


def iter_section_blocks(section: ContentSection) -> Iterator[tuple[str, str]]:
    yield from section.blocks
    if not section.visibility_key:
        return
    page = section.blocks[0][0] if section.blocks else section.page_slug
    yield page, section.visibility_key


def all_registry_block_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for section in CONTENT_SECTIONS:
        keys.update(iter_section_blocks(section))
    return keys


def build_content_sidebar_items() -> list[dict]:
    return [
        {
            'title': section.sidebar_title or section.title,
            'icon': section.sidebar_icon,
            'link': reverse_lazy(f'admin:core_{section.admin_model_name}_changelist'),
        }
        for section in CONTENT_SECTIONS
    ]
