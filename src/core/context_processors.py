from __future__ import annotations

from django.core.cache import cache

from src.catalog.models import Category, Product

from .models import SiteBlock, SiteSettings, SocialLink

SITE_BLOCKS_CACHE_KEY = 'oyra_site_blocks_v1'
SITE_BLOCKS_CACHE_TTL = 60
CATEGORIES_MENU_CACHE_KEY = 'oyra_categories_menu_v2'
CATEGORIES_MENU_CACHE_TTL = 60
HIDDEN_CATALOG_MENU_NAMES = ('Трактори', 'Обладнання СТО')


def _load_site_blocks() -> dict[str, SiteBlock]:
    cached = cache.get(SITE_BLOCKS_CACHE_KEY)
    if cached is not None:
        return cached

    blocks = {block.cache_key: block for block in SiteBlock.objects.filter(is_active=True)}
    cache.set(SITE_BLOCKS_CACHE_KEY, blocks, SITE_BLOCKS_CACHE_TTL)
    return blocks


def _ancestor_ids(seed_ids: set[int], parent_by_id: dict[int, int | None]) -> set[int]:
    """Усі id з seed + їхні предки (щоб батьки з товарами в листках лишались у меню)."""
    visible = set(seed_ids)
    for cid in list(seed_ids):
        pid = parent_by_id.get(cid)
        while pid is not None and pid not in visible:
            visible.add(pid)
            pid = parent_by_id.get(pid)
    return visible


def _build_categories_menu() -> list[Category]:
    """
    Кореневі категорії для дропдауна:
    - без прихованих гілок;
    - лише якщо є хоч один активний товар у категорії або нащадках;
    - підкатегорії теж лише з активними товарами в піддереві.
    """
    hidden = HIDDEN_CATALOG_MENU_NAMES
    cats = list(
        Category.objects.filter(is_active=True)
        .exclude(name__in=hidden)
        .order_by('sort_order', 'name')
        .only('id', 'name', 'slug', 'parent_id', 'sort_order')
    )
    if not cats:
        return []

    parent_by_id: dict[int, int | None] = {c.id: c.parent_id for c in cats}
    by_parent: dict[int | None, list[Category]] = {}
    for cat in cats:
        by_parent.setdefault(cat.parent_id, []).append(cat)

    product_cat_ids = set(
        Product.objects.filter(is_active=True, category_id__in=parent_by_id.keys())
        .values_list('category_id', flat=True)
        .distinct()
    )
    visible_ids = _ancestor_ids(product_cat_ids, parent_by_id)

    roots: list[Category] = []
    for root in by_parent.get(None, []):
        if root.id not in visible_ids:
            continue
        children = [child for child in by_parent.get(root.id, []) if child.id in visible_ids]
        # Атрибут для шаблону (не поле моделі)
        root.menu_children = children  # type: ignore[attr-defined]
        roots.append(root)
    return roots


def _categories_menu() -> list[Category]:
    cached = cache.get(CATEGORIES_MENU_CACHE_KEY)
    if cached is not None:
        return cached
    menu = _build_categories_menu()
    cache.set(CATEGORIES_MENU_CACHE_KEY, menu, CATEGORIES_MENU_CACHE_TTL)
    return menu


def site_context(request):
    settings_obj = SiteSettings.get_solo()
    social_links = list(SocialLink.objects.filter(is_active=True))
    youtube_link = next((item for item in social_links if item.network == 'youtube' and item.url), None)
    return {
        'site_settings': settings_obj,
        'site_blocks': _load_site_blocks(),
        'categories_menu': _categories_menu(),
        'social_links': social_links,
        'youtube_social_url': (
            youtube_link.url if youtube_link else settings_obj.youtube_url
        ),
    }
