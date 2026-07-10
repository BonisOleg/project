from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin
from unfold.admin import ModelAdmin

from src.core.admin_filters import (
    DropdownFiltersMixin,
    UkBooleanDropdownFilter,
    UkChoicesDropdownFilter,
)
from src.core.admin_utils import TinyMCEAdminMixin

from .models import (
    DropshippingApplication,
    FAQItem,
    NewsletterSubscription,
    ProductInstruction,
    StaticPage,
)


@admin.register(StaticPage)
class StaticPageAdmin(DropdownFiltersMixin, TinyMCEAdminMixin, ModelAdmin):
    list_display = ('title', 'slug', 'is_published')
    list_filter = [
        ('is_published', UkBooleanDropdownFilter),
    ]
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'slug')
    fieldsets = (
        ('Основне', {'fields': ('title', 'slug', 'content', 'is_published')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )


@admin.register(FAQItem)
class FAQItemAdmin(DropdownFiltersMixin, SortableAdminMixin, TinyMCEAdminMixin, ModelAdmin):
    list_display = ('question', 'is_published', 'sort_order')
    list_filter = [
        ('is_published', UkBooleanDropdownFilter),
    ]
    search_fields = ('question',)


@admin.register(ProductInstruction)
class ProductInstructionAdmin(DropdownFiltersMixin, ModelAdmin):
    list_display = ('title', 'sku', 'is_published')
    list_filter = [
        ('is_published', UkBooleanDropdownFilter),
    ]
    search_fields = ('title', 'sku')


@admin.register(DropshippingApplication)
class DropshippingApplicationAdmin(DropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'email', 'phone', 'city', 'status', 'created_at')
    list_filter = [
        ('status', UkChoicesDropdownFilter),
    ]
    search_fields = ('name', 'email', 'phone', 'city')
    readonly_fields = ('created_at',)


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(DropdownFiltersMixin, ModelAdmin):
    list_display = ('email', 'discount_sent', 'created_at')
    list_filter = [
        ('discount_sent', UkBooleanDropdownFilter),
    ]
    search_fields = ('email',)
    readonly_fields = ('created_at',)
