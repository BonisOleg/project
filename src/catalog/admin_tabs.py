from django.contrib import admin
from adminsortable2.admin import SortableAdminBase
from unfold.admin import ModelAdmin

from src.core.admin_utils import ImagePreviewMixin

from .admin_product_images import ProductImageInline, ProductImagesAdminMixin
from .models import MostViewedProduct, NewArrivalProduct, OnSaleProduct, TopSaleProduct


class _TabProductAdminBase(ProductImagesAdminMixin, SortableAdminBase, ModelAdmin):
    search_fields = ('name', 'sku')
    list_per_page = 25
    inlines = [ProductImageInline]
    readonly_fields = ('get_image_preview',)

    @admin.display(description='Фото')
    def get_image_preview(self, obj):
        image = obj.main_image
        if image and image.image:
            mixin = ImagePreviewMixin()
            mixin.image_field = 'image'
            return mixin.get_image_preview(image)
        return '—'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TopSaleProduct)
class TopSaleProductAdmin(_TabProductAdminBase):
    list_display = (
        'get_image_preview', 'name', 'sku', 'price', 'is_top_sale', 'sort_order',
    )
    list_editable = ('is_top_sale', 'sort_order')
    list_display_links = ('get_image_preview', 'name')
    ordering = ('-sort_order', '-created_at')
    fieldsets = (
        ('Основне', {
            'fields': ('name', 'sku', 'price', 'is_top_sale', 'sort_order'),
        }),
        ('Фото', {
            'fields': ('get_image_preview',),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .filter(is_top_sale=True)
            .select_related('category', 'brand')
            .prefetch_related('images')
        )


@admin.register(NewArrivalProduct)
class NewArrivalProductAdmin(_TabProductAdminBase):
    list_display = (
        'get_image_preview', 'name', 'sku', 'price', 'is_new', 'created_at',
    )
    list_editable = ('is_new',)
    list_display_links = ('get_image_preview', 'name')
    readonly_fields = ('get_image_preview', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        ('Основне', {
            'fields': ('name', 'sku', 'price', 'is_new', 'created_at'),
        }),
        ('Фото', {
            'fields': ('get_image_preview',),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .filter(is_new=True)
            .select_related('category', 'brand')
            .prefetch_related('images')
        )


@admin.register(MostViewedProduct)
class MostViewedProductAdmin(_TabProductAdminBase):
    list_display = (
        'get_image_preview', 'name', 'sku', 'price', 'views_count', 'is_top_sale',
    )
    list_editable = ('is_top_sale',)
    list_display_links = ('get_image_preview', 'name')
    readonly_fields = ('get_image_preview', 'views_count')
    ordering = ('-views_count', '-created_at')
    fieldsets = (
        ('Основне', {
            'fields': ('name', 'sku', 'price', 'views_count', 'is_top_sale'),
        }),
        ('Фото', {
            'fields': ('get_image_preview',),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .filter(is_active=True)
            .select_related('category', 'brand')
            .prefetch_related('images')
        )


@admin.register(OnSaleProduct)
class OnSaleProductAdmin(_TabProductAdminBase):
    list_display = (
        'get_image_preview', 'name', 'sku', 'price', 'old_price',
        'is_on_sale', 'sale_ends_at', 'sort_order',
    )
    list_editable = ('is_on_sale', 'sort_order')
    list_display_links = ('get_image_preview', 'name')
    ordering = ('-sort_order', '-created_at')
    fieldsets = (
        ('Основне', {
            'fields': (
                'name', 'sku', 'price', 'old_price',
                'is_on_sale', 'sale_ends_at', 'sort_order',
            ),
        }),
        ('Фото', {
            'fields': ('get_image_preview',),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .filter(is_on_sale=True)
            .select_related('category', 'brand')
            .prefetch_related('images')
        )
