from django.core.cache import cache
from django.db.models import Prefetch

from src.catalog.models import Category

from .models import SiteBlock, SiteSettings, SocialLink

SITE_BLOCKS_CACHE_KEY = 'oyra_site_blocks_v1'
SITE_BLOCKS_CACHE_TTL = 60


def _load_site_blocks() -> dict[str, SiteBlock]:
    cached = cache.get(SITE_BLOCKS_CACHE_KEY)
    if cached is not None:
        return cached

    blocks = {block.cache_key: block for block in SiteBlock.objects.filter(is_active=True)}
    cache.set(SITE_BLOCKS_CACHE_KEY, blocks, SITE_BLOCKS_CACHE_TTL)
    return blocks


def site_context(request):
    settings_obj = SiteSettings.get_solo()
    social_links = list(SocialLink.objects.filter(is_active=True))
    youtube_link = next((item for item in social_links if item.network == 'youtube' and item.url), None)
    categories_menu = Category.objects.filter(
        parent=None, is_active=True,
    ).prefetch_related(
        Prefetch('children', queryset=Category.objects.filter(is_active=True).order_by('sort_order')),
    ).order_by('sort_order')
    return {
        'site_settings': settings_obj,
        'site_blocks': _load_site_blocks(),
        'categories_menu': categories_menu,
        'social_links': social_links,
        'youtube_social_url': (
            youtube_link.url if youtube_link else settings_obj.youtube_url
        ),
    }
