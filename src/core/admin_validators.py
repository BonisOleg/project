"""
Валідація зображень для адмінки Oyra.
Перевіряє розмір файлу та мінімальні розміри сторони через Pillow.
"""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from PIL import Image

from src.core.admin_guidelines import IMAGE_PROFILES

ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP', 'GIF'}
ALLOWED_FORMATS_LABEL = 'JPG, PNG, WebP або GIF'


def validate_image_profile(image_file, profile_key: str) -> None:
    """
    Валідує завантажене зображення проти профілю.
    Викидає ValidationError якщо файл не відповідає вимогам.
    """
    if not image_file:
        return

    profile = IMAGE_PROFILES.get(profile_key, {})
    max_size_mb = profile.get('max_size_mb', 5)
    recommended = profile.get('recommended', '')

    max_bytes = max_size_mb * 1024 * 1024
    file_size = (
        image_file.size
        if hasattr(image_file, 'size')
        else len(image_file.read())
    )

    if file_size > max_bytes:
        raise ValidationError(
            f'Файл завеликий: {file_size / 1024 / 1024:.1f} МБ. '
            f'Максимальний дозволений розмір: {max_size_mb} МБ.'
        )

    try:
        if isinstance(image_file, (InMemoryUploadedFile, TemporaryUploadedFile)):
            image_file.seek(0)
            img = Image.open(image_file)
        else:
            img = Image.open(image_file)

        if img.format and img.format.upper() not in ALLOWED_FORMATS:
            raise ValidationError(
                f'Непідтримуваний формат: {img.format}. '
                f'Допустимі формати: {ALLOWED_FORMATS_LABEL}.'
            )

        if recommended:
            try:
                rec_w, rec_h = (int(x) for x in recommended.replace('×', 'x').split('x'))
                min_side = min(rec_w, rec_h) // 2
                w, h = img.size
                if w < min_side or h < min_side:
                    raise ValidationError(
                        f'Зображення замале: {w}×{h} пікселів. '
                        f'Рекомендований розмір: {recommended}.'
                    )
            except (ValueError, AttributeError):
                pass

        if hasattr(image_file, 'seek'):
            image_file.seek(0)

    except ValidationError:
        raise
    except Exception:
        pass
