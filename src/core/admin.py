from django.contrib import admin
from unfold.admin import ModelAdmin

from .admin_utils import ReadableUnfoldFieldsMixin, SingletonModelAdminMixin
from .admin_filters import (
    DropdownFiltersMixin,
    UkBooleanDropdownFilter,
    UkChoicesDropdownFilter,
)
from .models import SiteSettings, SocialLink


@admin.register(SiteSettings)
class SiteSettingsAdmin(ReadableUnfoldFieldsMixin, SingletonModelAdminMixin, ModelAdmin):
    fieldsets = (
        ('Основне', {'fields': ('site_name', 'phone', 'email', 'address', 'work_hours')}),
        ('Маркетинг', {'fields': ('newsletter_discount', 'free_delivery_from', 'meta_description')}),
        ('Сповіщення про замовлення', {
            'description': (
                'Глобальні контакти для дублюючих сповіщень про нові замовлення. '
                'Також можна увімкнути сповіщення окремому адміну в картці користувача.'
            ),
            'fields': ('notify_emails', 'notify_phones'),
        }),
        ('Реквізити (безготівковий розрахунок)', {
            'fields': (
                'bank_recipient', 'bank_iban', 'bank_edrpou',
                'bank_name', 'bank_details_note',
            ),
        }),
    )


@admin.register(SocialLink)
class SocialLinkAdmin(DropdownFiltersMixin, ReadableUnfoldFieldsMixin, ModelAdmin):
    list_display = ('network', 'url', 'sort_order', 'is_active')
    list_editable = ('url', 'sort_order', 'is_active')
    list_filter = [
        ('network', UkChoicesDropdownFilter),
        ('is_active', UkBooleanDropdownFilter),
    ]
    search_fields = ('url',)
    ordering = ('sort_order', 'id')
    list_display_links = ('network',)


from src.core import admin_site_content_proxies  # noqa: E402, F401
