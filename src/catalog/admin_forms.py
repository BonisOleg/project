"""Форми адмінки каталогу: мультизавантаження фото товару."""
from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from src.core.admin_guidelines import IMAGE_PROFILES, get_image_hint

_PRODUCT_MAX_BYTES = IMAGE_PROFILES['product']['max_size_mb'] * 1024 * 1024


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    """Поле для одного або кількох зображень."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'widget',
            MultipleFileInput(attrs={
                'accept': 'image/jpeg,image/png,image/webp,image/*',
                'class': 'product-bulk-images-input',
            }),
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if not data and not self.required:
            return []
        items = data if isinstance(data, (list, tuple)) else [data]
        image_field = forms.ImageField()
        cleaned = []
        for item in items:
            file_obj = single_file_clean(item, initial)
            if not file_obj:
                continue
            try:
                validated = image_field.clean(file_obj)
            except ValidationError as exc:
                raise ValidationError(exc.messages) from exc
            size = getattr(validated, 'size', None) or getattr(file_obj, 'size', None)
            if size is not None and size > _PRODUCT_MAX_BYTES:
                raise ValidationError(
                    f'Файл «{getattr(file_obj, "name", "image")}» перевищує '
                    f'{IMAGE_PROFILES["product"]["max_size_mb"]} МБ.'
                )
            if hasattr(validated, 'seek'):
                validated.seek(0)
            cleaned.append(validated)
        return cleaned


def build_product_admin_form(base_form):
    """Додає поле bulk_images до стандартної ModelForm адмінки."""

    class ProductAdminFormWithImages(base_form):
        bulk_images = MultipleImageField(
            label='Додати фото',
            required=False,
            help_text=(
                'Виберіть одне або кілька зображень одразу. '
                + get_image_hint('product')
            ),
        )

    ProductAdminFormWithImages.__name__ = getattr(base_form, '__name__', 'ProductAdminForm')
    return ProductAdminFormWithImages
