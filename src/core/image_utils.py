"""
Утиліта конвертації зображень у формат WebP для адмінки Oyra.
Використовується через Django-сигнали post_save.
"""
from __future__ import annotations

import io
import os

from django.core.files.base import ContentFile
from PIL import Image


WEBP_QUALITY = 85


def convert_field_to_webp(instance, field_name: str) -> bool:
    """
    Конвертує ImageField у WebP. Повертає True якщо конвертація відбулась.
    Безпечний для виклику з post_save: оновлює запис через queryset.update()
    щоб уникнути рекурсії сигналів.
    """
    field_file = getattr(instance, field_name, None)
    if not field_file or not field_file.name:
        return False

    name: str = field_file.name
    if name.lower().endswith('.webp'):
        return False

    try:
        field_file.open('rb')
        raw = field_file.read()
        field_file.close()
    except Exception:
        return False

    try:
        img = Image.open(io.BytesIO(raw))
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGBA')
        else:
            img = img.convert('RGB')

        buf = io.BytesIO()
        img.save(buf, format='WEBP', quality=WEBP_QUALITY, method=4)
        buf.seek(0)
    except Exception:
        return False

    base, _ = os.path.splitext(name)
    new_name = base + '.webp'
    new_content = ContentFile(buf.read(), name=os.path.basename(new_name))

    storage = field_file.storage

    try:
        old_path = field_file.path
    except (NotImplementedError, ValueError):
        old_path = None

    saved_name = storage.save(new_name, new_content)

    if old_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except OSError:
            pass

    model_class = type(instance)
    model_class.objects.filter(pk=instance.pk).update(**{field_name: saved_name})

    setattr(field_file, 'name', saved_name)

    return True
