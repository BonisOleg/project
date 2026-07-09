from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin
from unfold.admin import ModelAdmin

from src.core.admin_utils import TinyMCEAdminMixin

from .models import (
    DropshippingApplication,
    FAQItem,
    NewsletterSubscription,
    ProductInstruction,
    StaticPage,
)


@admin.register(StaticPage)
class StaticPageAdmin(TinyMCEAdminMixin, ModelAdmin):
    list_display = ('title', 'slug', 'is_published')
    list_filter = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'slug')
    fieldsets = (
        ('Основне', {'fields': ('title', 'slug', 'content', 'is_published')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )


@admin.register(FAQItem)
class FAQItemAdmin(SortableAdminMixin, TinyMCEAdminMixin, ModelAdmin):
    list_display = ('question', 'is_published', 'sort_order')
    list_filter = ('is_published',)
    search_fields = ('question',)


@admin.register(ProductInstruction)
class ProductInstructionAdmin(ModelAdmin):
    list_display = ('title', 'sku', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('title', 'sku')


@admin.register(DropshippingApplication)
class DropshippingApplicationAdmin(ModelAdmin):
    list_display = ('name', 'email', 'phone', 'city', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    list_filter_submit = True
    search_fields = ('name', 'email', 'phone', 'city')
    readonly_fields = ('created_at',)


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(ModelAdmin):
    list_display = ('email', 'discount_sent', 'created_at')
    list_filter = ('discount_sent',)
    search_fields = ('email',)
    readonly_fields = ('created_at',)
