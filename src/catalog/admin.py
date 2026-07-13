from django import forms
from django.contrib import admin
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from adminsortable2.admin import SortableAdminMixin
from unfold.admin import ModelAdmin, TabularInline

from src.core.admin_filters import (
    DropdownFiltersMixin,
    UkBooleanDropdownFilter,
    UkChoicesDropdownFilter,
    UkRelatedDropdownFilter,
)
from src.core.admin_guidelines import get_image_hint
from src.core.admin_utils import ImagePreviewMixin, TinyMCEAdminMixin

from .admin_product_images import ProductImageInline, ProductImagesAdminMixin
from .models import (
    AttributeGroup,
    Brand,
    CatalogFilter,
    Category,
    Product,
    ProductAttribute,
)
from . import admin_tabs  # noqa: F401

_CATEGORY_IMAGE_HINT = (
    get_image_hint('category')
    + ' Якщо фото не завантажено — на сайті показується іконка категорії (зі списку або власний файл).'
)


class ProductAttributeInline(TabularInline):
    model = ProductAttribute
    extra = 1
    autocomplete_fields = ('group',)


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'color': forms.TextInput(attrs={
                'type': 'color',
                'style': 'width: 4.5rem; height: 2.5rem; padding: 0;',
            }),
        }


@admin.register(Category)
class CategoryAdmin(DropdownFiltersMixin, SortableAdminMixin, ImagePreviewMixin, TinyMCEAdminMixin, ModelAdmin):
    form = CategoryAdminForm
    list_display = ('name', 'parent', 'get_color_swatch', 'get_image_preview', 'is_active', 'sort_order')
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
        ('Іконка та колір', {'fields': (
            'icon_key', 'icon_file', 'color',
        )}),
        ('Відображення на сайті', {'fields': ('sort_order', 'is_active')}),
        ('SEO (пошукові системи)', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'image':
            field.help_text = _CATEGORY_IMAGE_HINT
        if db_field.name == 'icon_key':
            field.help_text = 'Оберіть одну з 12 готових іконок або завантажте власний файл нижче.'
        if db_field.name == 'icon_file':
            field.help_text = 'Формати: SVG, PNG, JPG. Власний файл має пріоритет над іконкою зі списку.'
        if db_field.name == 'color':
            field.help_text = 'Колір акценту категорії на головній і в каталозі.'
        if db_field.name == 'slug':
            field.help_text = 'Частина адреси сторінки в URL. Заповнюється автоматично з назви.'
        return field

    @admin.display(description='Колір')
    def get_color_swatch(self, obj):
        color = obj.resolved_color() if obj else '#2453E0'
        return format_html(
            '<span style="display:inline-block;width:1.25rem;height:1.25rem;border-radius:50%;'
            'background:{};border:1px solid #ddd;vertical-align:middle"></span> {}',
            color, color,
        )

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
        ctx = {'icon_key': obj.resolved_icon_key()}
        if obj.icon_file:
            ctx['icon_file_url'] = obj.icon_file.url
        svg = render_to_string('partials/category_icon.html', ctx)
        return format_html(
            '<span class="category-admin-icon-preview" style="color:{};display:inline-flex;'
            'width:2.5rem;height:2.5rem;align-items:center;justify-content:center;'
            'border-radius:0.5rem;background:color-mix(in srgb, {} 14%, white)">{}</span>'
            '<span class="product-image-upload-hint">Іконка категорії</span>',
            obj.resolved_color(), obj.resolved_color(), mark_safe(svg),
        )


@admin.register(CatalogFilter)
class CatalogFilterAdmin(DropdownFiltersMixin, SortableAdminMixin, ModelAdmin):
    list_display = (
        'name', 'filter_type', 'attribute_name',
        'is_active', 'open_by_default', 'sort_order',
    )
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
        ('filter_type', UkChoicesDropdownFilter),
        ('open_by_default', UkBooleanDropdownFilter),
    ]
    search_fields = ('name', 'attribute_name')
    fieldsets = (
        ('Основне', {'fields': (
            'name', 'filter_type', 'attribute_name', 'fallback_values',
        )}),
        ('Відображення на сайті', {'fields': (
            'sort_order', 'is_active', 'open_by_default',
        )}),
    )


@admin.register(Brand)
class BrandAdmin(DropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
    ]
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(
    ProductImagesAdminMixin,
    DropdownFiltersMixin,
    SortableAdminMixin,
    TinyMCEAdminMixin,
    ModelAdmin,
):
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
                'short_description', 'description',
            ),
        }),
        ('Фото', {
            'fields': ('get_image_preview',),
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
        ('SEO (пошукові системи)', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('Статистика', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Головне фото')
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
