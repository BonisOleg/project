from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RelatedDropdownFilter

from .models import Review


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ('product', 'author_name', 'rating', 'is_published', 'created_at')
    list_filter = [
        ('is_published', ChoicesDropdownFilter),
        ('rating', ChoicesDropdownFilter),
        ('product', RelatedDropdownFilter),
    ]
    list_filter_submit = True
    search_fields = ('author_name', 'text', 'product__name')
    autocomplete_fields = ('product', 'user')
    readonly_fields = ('created_at',)
