from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'used_count', 'valid_until')
    list_filter = ('is_active', 'discount_type')
    list_filter_submit = True
    search_fields = ('code',)
    readonly_fields = ('used_count',)
