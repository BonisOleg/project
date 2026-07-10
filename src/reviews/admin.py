from django.contrib import admin
from unfold.admin import ModelAdmin

from src.core.admin_filters import (
    DropdownFiltersMixin,
    UkChoicesDropdownFilter,
    UkRelatedDropdownFilter,
)

from .models import Review


@admin.register(Review)
class ReviewAdmin(DropdownFiltersMixin, ModelAdmin):
    list_display = ('product', 'author_name', 'rating', 'is_published', 'created_at')
    list_filter = [
        ('is_published', UkChoicesDropdownFilter),
        ('rating', UkChoicesDropdownFilter),
        ('product', UkRelatedDropdownFilter),
    ]
    search_fields = ('author_name', 'text', 'product__name')
    autocomplete_fields = ('product', 'user')
    readonly_fields = ('created_at',)
