from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .admin_utils import ReadableUnfoldFieldsMixin, SingletonModelAdminMixin
from .admin_filters import (
    DropdownFiltersMixin,
    UkBooleanDropdownFilter,
    UkChoicesDropdownFilter,
)
from .admin_site_content_widgets import CmsAdminTextInputWidget
from .models import SitePhone, SiteSettings, SocialLink


class SitePhoneInline(TabularInline):
    model = SitePhone
    extra = 1
    min_num = 0
    fields = ('phone', 'is_active')
    ordering = ('sort_order', 'id')
    verbose_name = 'Телефон'
    verbose_name_plural = 'Телефони'

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'phone':
            kwargs['widget'] = CmsAdminTextInputWidget(attrs={'type': 'tel', 'inputmode': 'tel'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(SiteSettings)
class SiteSettingsAdmin(ReadableUnfoldFieldsMixin, SingletonModelAdminMixin, ModelAdmin):
    inlines = [SitePhoneInline]
    fieldsets = (
        ('Основне', {'fields': ('site_name', 'email', 'address', 'work_hours')}),
        ('Маркетинг', {'fields': ('newsletter_discount', 'free_delivery_from', 'meta_description')}),
        ('Сповіщення про замовлення', {
            'description': (
                'Глобальні контакти для дублюючих сповіщень про нові замовлення. '
                'Також можна увімкнути сповіщення окремому адміну в картці користувача.'
            ),
            'fields': ('notify_emails', 'notify_phones'),
        }),
        ('Безготівкова оплата', {
            'description': 'Реквізити ФОП редагуються в розділі «Вміст сторінок → Оферта — Реквізити».',
            'fields': ('bank_details_note',),
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
