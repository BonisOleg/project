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
from .admin_supplier_import import SupplierImportAdminMixin
from .models import (
    AttributeGroup,
    Brand,
    CatalogFilter,
    Category,
    Product,
    ProductAttribute,
    Supplier,
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
class CategoryAdmin(DropdownFiltersMixin, SortableAdminMixin, TinyMCEAdminMixin, ModelAdmin):
    form = CategoryAdminForm
    list_display = (
        'name', 'parent', 'get_color_swatch', 'get_list_card_preview',
        'is_active', 'sort_order',
    )
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
        ('parent', UkRelatedDropdownFilter),
    ]
    list_select_related = ('parent', 'parent__parent')
    ordering = ('sort_order', 'name')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    readonly_fields = ('get_form_card_preview',)
    fieldsets = (
        ('Основне', {'fields': (
            'name', 'slug', 'parent', 'description',
        )}),
        ('Фото категорії', {
            'description': (
                'Фото на картці категорії на головній і в каталозі '
                '(показуються кореневі категорії). '
                'JPG, PNG або WebP. Рекомендований розмір: 800×600 пікселів (4:3). '
                'Макс. 1 МБ. Без власного фото на сайті — іконка; у превʼю адмінки '
                'підтягнеться фото батьківської, якщо воно є.'
            ),
            'fields': ('image', 'get_form_card_preview'),
            'classes': ('collapse',),
        }),
        ('Іконка та колір', {
            'fields': ('icon_key', 'icon_file', 'color'),
            'classes': ('collapse',),
        }),
        ('Відображення на сайті', {'fields': ('sort_order', 'is_active')}),
        ('SEO (пошукові системи)', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'image':
            field.label = 'Фото картки'
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

    @staticmethod
    def _has_own_card_image(obj) -> bool:
        return bool(obj and obj.pk and getattr(obj.image, 'name', None))

    def _icon_fallback_html(self, obj):
        ctx = {'icon_key': obj.resolved_icon_key()}
        if obj.icon_file:
            ctx['icon_file_url'] = obj.icon_file.url
        svg = render_to_string('partials/category_icon.html', ctx)
        return format_html(
            '<span class="category-admin-icon-preview" style="color:{};'
            'background:color-mix(in srgb, {} 14%, white)">{}</span>',
            obj.resolved_color(), obj.resolved_color(), mark_safe(svg),
        )

    @admin.display(description='Превʼю картки')
    def get_list_card_preview(self, obj):
        """Список: власне фото → фото предка → іконка."""
        if not obj or not obj.pk:
            return '—'
        image = obj.resolved_card_image()
        if image:
            title = 'Фото картки' if self._has_own_card_image(obj) else 'Фото батьківської категорії'
            return format_html(
                '<img src="{}" alt="" class="category-admin-photo-preview '
                'category-admin-photo-preview--list" title="{}">',
                image.url,
                title,
            )
        return format_html(
            '<div class="category-admin-photo-wrap category-admin-photo-wrap--list">'
            '{}'
            '<span class="product-image-upload-hint">Іконка (немає фото)</span>'
            '</div>',
            self._icon_fallback_html(obj),
        )

    @admin.display(description='Превʼю на сайті')
    def get_form_card_preview(self, obj):
        """Форма: власне фото → фото предка → іконка-фолбек."""
        if not obj or not obj.pk:
            return format_html(
                '<span class="product-image-upload-hint">'
                'Збережіть категорію, щоб побачити превʼю.</span>',
            )
        image = obj.resolved_card_image()
        if image and self._has_own_card_image(obj):
            return format_html(
                '<div class="category-admin-photo-wrap">'
                '<img src="{}" alt="" class="category-admin-photo-preview">'
                '<span class="product-image-upload-hint">'
                'Поточне фото картки на сайті. Можна замінити полем вище.'
                '</span></div>',
                image.url,
            )
        if image:
            return format_html(
                '<div class="category-admin-photo-wrap">'
                '<img src="{}" alt="" class="category-admin-photo-preview">'
                '<span class="product-image-upload-hint">'
                'Власного фото немає — показано фото батьківської «{}». '
                'На головній в ряду карток показуються лише корені з власним фото. '
                'Завантажте фото вище, щоб задати окреме зображення для цієї категорії.'
                '</span></div>',
                image.url,
                obj.parent.name if obj.parent_id else '',
            )
        return format_html(
            '<div class="category-admin-photo-wrap">'
            '{}'
            '<span class="product-image-upload-hint">'
            'Фото немає ні в цієї, ні в батьківських категорій — '
            'на сайті показується іконка. Завантажте фото вище.'
            '</span></div>',
            self._icon_fallback_html(obj),
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


@admin.register(Supplier)
class SupplierAdmin(SupplierImportAdminMixin, DropdownFiltersMixin, ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'products_count', 'updated_at')
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
    ]
    search_fields = ('name', 'code')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Товарів')
    def products_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(
    ProductImagesAdminMixin,
    DropdownFiltersMixin,
    SortableAdminMixin,
    TinyMCEAdminMixin,
    ModelAdmin,
):
    list_display = (
        'get_image_preview', 'name', 'sku', 'category',
        'quick_price', 'stock_quantity', 'quick_availability', 'is_active',
    )
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
        ('availability', UkChoicesDropdownFilter),
        ('category', UkRelatedDropdownFilter),
        ('brand', UkRelatedDropdownFilter),
        ('supplier', UkRelatedDropdownFilter),
        ('is_top_sale', UkBooleanDropdownFilter),
        ('is_new', UkBooleanDropdownFilter),
        ('is_on_sale', UkBooleanDropdownFilter),
    ]
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category', 'brand', 'supplier')
    readonly_fields = ('get_image_preview', 'views_count', 'created_at', 'updated_at')
    inlines = [ProductImageInline, ProductAttributeInline]
    fieldsets = (
        ('Основне', {
            'fields': (
                'name', 'slug', 'sku', 'category', 'brand', 'supplier',
                'short_description', 'description',
            ),
        }),
        ('Фото', {
            'fields': ('get_image_preview',),
        }),
        ('Ціни та наявність', {
            'fields': (
                'price', 'old_price', 'stock_quantity', 'availability', 'sale_ends_at',
            ),
        }),
        ('Мітки', {
            'fields': (
                'is_active', 'is_top_sale', 'is_new', 'is_on_sale',
                'requires_prepayment', 'sort_order',
            ),
            'classes': ('collapse',),
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

    @admin.display(description='Ціна')
    def quick_price(self, obj):
        return format_html(
            '<input type="number" step="0.01" min="0" class="oyra-quick-price" '
            'data-product-id="{}" value="{}" aria-label="Ціна">'
            '<span class="oyra-quick-status" aria-live="polite"></span>',
            obj.pk,
            obj.price,
        )

    @admin.display(description='Наявність')
    def quick_availability(self, obj):
        options = []
        for value, label in Product.AVAILABILITY_CHOICES:
            selected = ' selected' if obj.availability == value else ''
            options.append(f'<option value="{value}"{selected}>{label}</option>')
        return mark_safe(
            f'<select class="oyra-quick-availability" data-product-id="{obj.pk}" '
            f'aria-label="Наявність">{"".join(options)}</select>'
            f'<span class="oyra-quick-status" aria-live="polite"></span>'
        )

    class Media:
        js = ('js/admin/product_quick_edit.js',)
        css = {'all': ('css/admin/product_quick_edit.css',)}


@admin.register(AttributeGroup)
class AttributeGroupAdmin(SortableAdminMixin, ModelAdmin):
    list_display = ('name', 'sort_order')
    search_fields = ('name',)
