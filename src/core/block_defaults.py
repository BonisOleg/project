HERO_LEAD_DEFAULT = (
    'Якість, доступні ціни та швидка доставка по всій Україні. '
    'Оплата через LiqPay — карткою або Apple Pay.'
)

BLOCK_FIELD_LABELS: dict[tuple[str, str], str] = {
    ('home', 'hero_eyebrow'): 'Мітка (eyebrow)',
    ('home', 'hero_title'): 'Заголовок',
    ('home', 'hero_lead'): 'Підзаголовок',
    ('home', 'hero_image'): 'Фото hero',
    ('home', 'hero_image_alt'): 'Alt-текст фото',
    ('home', 'hero_btn_catalog'): 'Кнопка «Каталог»',
    ('home', 'hero_btn_sale'): 'Кнопка «Акції»',
    ('home', 'products_section_title'): 'Заголовок секції',
    ('home', 'categories_section_title'): 'Заголовок секції',
    ('home', 'benefits_section_title'): 'Заголовок секції',
    ('home', 'benefit_1_title'): 'Перевага 1 — заголовок',
    ('home', 'benefit_1_text'): 'Перевага 1 — текст',
    ('home', 'benefit_2_title'): 'Перевага 2 — заголовок',
    ('home', 'benefit_2_text'): 'Перевага 2 — текст',
    ('home', 'benefit_3_title'): 'Перевага 3 — заголовок',
    ('home', 'benefit_3_text'): 'Перевага 3 — текст ({discount} = знижка підписки)',
    ('home', 'benefit_4_title'): 'Перевага 4 — заголовок',
    ('home', 'benefit_4_text'): 'Перевага 4 — текст',
    ('home', 'about_section_title'): 'Заголовок',
    ('home', 'about_section_lead'): 'Текст',
    ('home', 'blog_section_title'): 'Заголовок секції',
    ('site', 'header_search_placeholder'): 'Placeholder пошуку',
    ('site', 'header_nav_catalog_label'): 'Підпис «Каталог»',
    ('site', 'header_nav_sale_label'): 'Підпис «Акції»',
    ('site', 'header_nav_news_label'): 'Підпис «Новини»',
    ('site', 'header_search_visible'): 'Показувати поле пошуку',
    ('site', 'header_nav_catalog_visible'): 'Показувати «Каталог»',
    ('site', 'header_nav_sale_visible'): 'Показувати «Акції»',
    ('site', 'header_nav_news_visible'): 'Показувати «Новини»',
    ('site', 'header_action_phone_visible'): 'Показувати іконку телефону',
    ('site', 'header_action_wishlist_visible'): 'Показувати «Обране»',
    ('site', 'header_action_compare_visible'): 'Показувати «Порівняння»',
    ('site', 'header_action_cart_visible'): 'Показувати «Кошик»',
    ('site', 'header_action_login_visible'): 'Показувати «Вхід» / «Кабінет»',
    ('site', 'header_nav_delivery_visible'): 'Показувати «Доставка» (моб. меню)',
    ('site', 'header_nav_about_visible'): 'Показувати «Про нас» (моб. меню)',
}

BLOCK_DEFAULTS: dict[tuple[str, str], str] = {
    ('home', 'hero_section_visible'): '1',
    ('home', 'hero_eyebrow'): 'Oyra — преміальний магазин',
    ('home', 'hero_title'): 'Корисні товари для дому, офісу та відпочинку',
    ('home', 'hero_lead'): HERO_LEAD_DEFAULT,
    ('home', 'hero_image_alt'): 'Діти стрибають на батуті у дворі',
    ('home', 'hero_btn_catalog'): 'Переглянути каталог',
    ('home', 'hero_btn_sale'): 'Акції',
    ('home', 'products_section_visible'): '1',
    ('home', 'products_section_title'): 'Популярні товари',
    ('home', 'categories_section_visible'): '1',
    ('home', 'categories_section_title'): 'Популярні категорії',
    ('home', 'benefits_section_visible'): '1',
    ('home', 'benefits_section_title'): 'Наші переваги',
    ('home', 'benefit_1_title'): 'Краща ціна на ринку',
    ('home', 'benefit_1_text'): 'Працюємо напряму з виробниками — без зайвих націнок.',
    ('home', 'benefit_2_title'): 'Доставка 1–3 дні',
    ('home', 'benefit_2_text'): 'Нова Пошта та Укрпошта по всій Україні.',
    ('home', 'benefit_3_title'): 'Система знижок',
    ('home', 'benefit_3_text'): 'Промокоди та знижка {discount}% за підписку.',
    ('home', 'benefit_4_title'): 'Повернення 14 днів',
    ('home', 'benefit_4_text'): 'Повернення товару та коштів протягом двох тижнів.',
    ('home', 'about_section_visible'): '1',
    ('home', 'about_section_title'): 'Oyra — сучасний інтернет-магазин',
    ('home', 'about_section_lead'): (
        'Інтернет-магазин Oyra пропонує широкий асортимент товарів для дому, офісу, '
        'саду та відпочинку. Ми докладаємо зусиль, щоб ваші покупки були зручними та безпечними.'
    ),
    ('home', 'blog_section_visible'): '1',
    ('home', 'blog_section_title'): 'Блог',
    ('site', 'header_search_placeholder'): 'Пошук товарів...',
    ('site', 'header_nav_catalog_label'): 'Каталог',
    ('site', 'header_nav_sale_label'): 'Акції',
    ('site', 'header_nav_news_label'): 'Новини',
    ('site', 'header_search_visible'): '1',
    ('site', 'header_nav_catalog_visible'): '1',
    ('site', 'header_nav_sale_visible'): '1',
    ('site', 'header_nav_news_visible'): '1',
    ('site', 'header_action_phone_visible'): '1',
    ('site', 'header_action_wishlist_visible'): '1',
    ('site', 'header_action_compare_visible'): '1',
    ('site', 'header_action_cart_visible'): '1',
    ('site', 'header_action_login_visible'): '1',
    ('site', 'header_nav_delivery_visible'): '1',
    ('site', 'header_nav_about_visible'): '1',
}

BLOCK_CONTENT_TYPES: dict[tuple[str, str], str] = {
    ('home', 'hero_image'): 'image',
}

MULTILINE_KEYS: frozenset[str] = frozenset({
    'hero_lead',
    'about_section_lead',
    'benefit_1_text',
    'benefit_2_text',
    'benefit_3_text',
    'benefit_4_text',
})

INLINE_KEYS: frozenset[str] = frozenset({
    'hero_eyebrow',
    'hero_title',
    'hero_image_alt',
    'hero_btn_catalog',
    'hero_btn_sale',
    'products_section_title',
    'categories_section_title',
    'benefits_section_title',
    'benefit_1_title',
    'benefit_2_title',
    'benefit_3_title',
    'benefit_4_title',
    'about_section_title',
    'blog_section_title',
    'header_search_placeholder',
    'header_nav_catalog_label',
    'header_nav_sale_label',
    'header_nav_news_label',
})

VISIBILITY_SUFFIX = '_visible'


def is_visibility_key(key: str) -> bool:
    return key.endswith(VISIBILITY_SUFFIX)
