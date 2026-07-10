from django.contrib import admin
from unfold.admin import ModelAdmin

from .admin_utils import ReadableUnfoldFieldsMixin, SingletonModelAdminMixin
from .models import SiteSettings, SocialLink


@admin.register(SiteSettings)
class SiteSettingsAdmin(ReadableUnfoldFieldsMixin, SingletonModelAdminMixin, ModelAdmin):
    fieldsets = (
        ('Основне', {'fields': ('site_name', 'phone', 'email', 'address', 'work_hours')}),
        ('Маркетинг', {'fields': ('newsletter_discount', 'free_delivery_from', 'meta_description')}),
    )


@admin.register(SocialLink)
class SocialLinkAdmin(ReadableUnfoldFieldsMixin, ModelAdmin):
    list_display = ('network', 'url', 'sort_order', 'is_active')
    list_editable = ('url', 'sort_order', 'is_active')
    list_filter = ('network', 'is_active')
    search_fields = ('url',)
    ordering = ('sort_order', 'id')
    list_display_links = ('network',)


from src.core import admin_site_content_proxies  # noqa: E402, F401
