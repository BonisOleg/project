from django.contrib import admin
from unfold.admin import ModelAdmin

from .admin_utils import ReadableUnfoldFieldsMixin, SingletonModelAdminMixin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(ReadableUnfoldFieldsMixin, SingletonModelAdminMixin, ModelAdmin):
    fieldsets = (
        ('Основне', {'fields': ('site_name', 'phone', 'email', 'address', 'work_hours')}),
        ('Соцмережі', {'fields': ('facebook_url', 'youtube_url', 'instagram_url')}),
        ('Маркетинг', {'fields': ('newsletter_discount', 'free_delivery_from', 'meta_description')}),
    )


from src.core import admin_site_content_proxies  # noqa: E402, F401
