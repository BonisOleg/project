from django.contrib import admin
from unfold.admin import ModelAdmin

from src.core.admin_filters import (
    DropdownFiltersMixin,
    UkBooleanDropdownFilter,
    UkChoicesDropdownFilter,
)

from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(DropdownFiltersMixin, ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'used_count', 'valid_until')
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
        ('discount_type', UkChoicesDropdownFilter),
    ]
    search_fields = ('code',)
    readonly_fields = ('used_count',)
