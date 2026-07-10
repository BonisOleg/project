"""Спільна галерея фото товару для ProductAdmin і вкладок каталогу."""
from __future__ import annotations

from django.contrib import admin
from django.db.models import Max
from django.utils.html import format_html
from adminsortable2.admin import SortableInlineAdminMixin
from unfold.admin import TabularInline

from src.core.admin_guidelines import get_image_hint

from .admin_forms import build_product_admin_form
from .models import ProductImage

_PRODUCT_IMAGE_HINT = get_image_hint('product')


class ProductImageInline(SortableInlineAdminMixin, TabularInline):
    model = ProductImage
    extra = 1
    verbose_name = 'Фото'
    verbose_name_plural = 'Галерея фото'
    fields = ('image', 'get_image_preview', 'alt_text', 'is_main', 'sort_order')
    readonly_fields = ('get_image_preview',)
    ordering = ('sort_order', 'pk')

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


_PHOTO_FIELDSET_DESCRIPTION = (
    'Додайте одне або кілька фото. Нижче в «Галерея фото» можна '
    'змінити порядок (drag-and-drop), обрати головне та видалити.'
)


class ProductImagesAdminMixin:
    """Окреме поле мультизавантаження + галерея фото у формі товару."""

    def get_form(self, request, obj=None, **kwargs):
        from django.contrib.admin.utils import flatten_fieldsets

        readonly = set(self.get_readonly_fields(request, obj))
        fields = [
            name
            for name in flatten_fieldsets(self.get_fieldsets(request, obj))
            if name != 'bulk_images' and name not in readonly
        ]
        kwargs['fields'] = fields
        base_form = super().get_form(request, obj, **kwargs)
        return build_product_admin_form(base_form)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        result = []
        for name, options in fieldsets:
            opts = dict(options)
            fields = list(opts.get('fields', ()))
            if name == 'Фото' and 'bulk_images' not in fields:
                fields = ['bulk_images', *fields]
                opts['fields'] = tuple(fields)
                opts.setdefault('description', _PHOTO_FIELDSET_DESCRIPTION)
            result.append((name, opts))
        return result

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        files = form.cleaned_data.get('bulk_images') or []
        if not files:
            return

        product = form.instance
        max_order = product.images.aggregate(m=Max('sort_order'))['m'] or 0
        has_main = product.images.filter(is_main=True).exists()

        for index, uploaded in enumerate(files):
            ProductImage.objects.create(
                product_id=product.pk,
                image=uploaded,
                sort_order=max_order + index + 1,
                is_main=(not has_main and index == 0),
            )
