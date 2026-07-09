from django.contrib import admin
from django.utils.html import format_html
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from unfold.admin import ModelAdmin, TabularInline

from src.core.admin_utils import ImagePreviewMixin, TinyMCEAdminMixin

from .models import (
    AttributeGroup,
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductImage,
)


class ProductImageInline(SortableInlineAdminMixin, TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'get_image_preview', 'alt_text', 'is_main', 'sort_order')
    readonly_fields = ('get_image_preview',)

    @admin.display(description='Превʼю')
    def get_image_preview(self, obj):
        if obj and obj.pk and obj.image:
            return format_html(
                '<img src="{}" alt="" style="max-height:56px;border-radius:8px;object-fit:cover;">',
                obj.image.url,
            )
        return '—'


class ProductAttributeInline(TabularInline):
    model = ProductAttribute
    extra = 1
    autocomplete_fields = ('group',)


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, ImagePreviewMixin, TinyMCEAdminMixin, ModelAdmin):
    list_display = ('name', 'parent', 'get_image_preview', 'is_active', 'sort_order')
    list_filter = ('is_active', 'parent')
    list_filter_submit = True
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    readonly_fields = ('get_image_preview',)
    fieldsets = (
        ('Основне', {'fields': ('name', 'slug', 'parent', 'description', 'image', 'get_image_preview', 'icon')}),
        ('Відображення', {'fields': ('sort_order', 'is_active')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(SortableAdminMixin, TinyMCEAdminMixin, ModelAdmin):
    list_display = (
        'get_image_preview', 'name', 'sku', 'category', 'price', 'availability', 'is_active',
    )
    list_filter = ('is_active', 'category', 'brand', 'availability', 'is_top_sale', 'is_new', 'is_on_sale')
    list_filter_submit = True
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category', 'brand')
    readonly_fields = ('get_image_preview', 'views_count', 'created_at', 'updated_at')
    inlines = [ProductImageInline, ProductAttributeInline]
    fieldsets = (
        ('Основне', {
            'fields': (
                'name', 'slug', 'sku', 'category', 'brand',
                'short_description', 'description', 'get_image_preview',
            ),
        }),
        ('Ціни та наявність', {
            'fields': ('price', 'old_price', 'availability', 'sale_ends_at'),
        }),
        ('Мітки', {
            'fields': ('is_active', 'is_top_sale', 'is_new', 'is_on_sale', 'requires_prepayment', 'sort_order'),
        }),
        ('Медіа', {
            'fields': ('youtube_url', 'video_url', 'has_video'),
            'classes': ('collapse',),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('Статистика', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Фото')
    def get_image_preview(self, obj):
        image = obj.main_image
        if image and image.image:
            mixin = ImagePreviewMixin()
            mixin.image_field = 'image'
            return mixin.get_image_preview(image)
        return '—'


@admin.register(AttributeGroup)
class AttributeGroupAdmin(SortableAdminMixin, ModelAdmin):
    list_display = ('name', 'sort_order')
    search_fields = ('name',)
