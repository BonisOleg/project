from django.contrib import admin
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from unfold.admin import ModelAdmin, TabularInline

from src.core.admin_filters import (
    DropdownFiltersMixin,
    UkBooleanDropdownFilter,
    UkChoicesDropdownFilter,
    UkRelatedDropdownFilter,
)
from src.core.admin_guidelines import get_image_hint
from src.core.admin_utils import ImagePreviewMixin, TinyMCEAdminMixin

from .models import (
    AttributeGroup,
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductImage,
)
from . import admin_tabs  # noqa: F401

_PRODUCT_IMAGE_HINT = get_image_hint('product')
_CATEGORY_IMAGE_HINT = (
    get_image_hint('category')
    + ' Якщо фото не завантажено — на сайті показується вбудована іконка категорії (див. превʼю).'
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
                '<img src="{}" alt="" class="product-image-inline-preview">'
                '<span class="product-image-upload-hint">{}</span>',
                obj.image.url,
                _PRODUCT_IMAGE_HINT,
            )
        return format_html(
            '<span class="product-image-upload-hint">{}</span>',
            _PRODUCT_IMAGE_HINT,
        )


class ProductAttributeInline(TabularInline):
    model = ProductAttribute
    extra = 1
    autocomplete_fields = ('group',)


@admin.register(Category)
class CategoryAdmin(DropdownFiltersMixin, SortableAdminMixin, ImagePreviewMixin, TinyMCEAdminMixin, ModelAdmin):
    list_display = ('name', 'parent', 'get_image_preview', 'is_active', 'sort_order')
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
        ('parent', UkRelatedDropdownFilter),
    ]
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    readonly_fields = ('get_image_preview',)
    fieldsets = (
        ('Основне', {'fields': (
            'name', 'slug', 'parent', 'description',
            'image', 'get_image_preview',
        )}),
        ('Відображення', {'fields': ('sort_order', 'is_active')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'image':
            field.help_text = _CATEGORY_IMAGE_HINT
        return field

    @admin.display(description='Іконка на сайті')
    def get_image_preview(self, obj):
        if not obj or not obj.pk:
            return '—'
        if obj.image:
            return format_html(
                '<img src="{}" alt="" class="product-image-inline-preview">'
                '<span class="product-image-upload-hint">Завантажене фото</span>',
                obj.image.url,
            )
        if obj.slug:
            svg = render_to_string('partials/category_icon.html', {'slug': obj.slug})
            return format_html(
                '<span class="category-admin-icon-preview" title="Вбудована іконка категорії">{}</span>'
                '<span class="product-image-upload-hint">Вбудована іконка (як на головній)</span>',
                mark_safe(svg),
            )
        return '—'


@admin.register(Brand)
class BrandAdmin(DropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
    ]
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(DropdownFiltersMixin, SortableAdminMixin, TinyMCEAdminMixin, ModelAdmin):
    list_display = (
        'get_image_preview', 'name', 'sku', 'category', 'price', 'availability', 'is_active',
    )
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
        ('availability', UkChoicesDropdownFilter),
        ('category', UkRelatedDropdownFilter),
        ('brand', UkRelatedDropdownFilter),
        ('is_top_sale', UkBooleanDropdownFilter),
        ('is_new', UkBooleanDropdownFilter),
        ('is_on_sale', UkBooleanDropdownFilter),
    ]
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
