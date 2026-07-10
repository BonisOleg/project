from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Post


@receiver(post_save, sender=Post)
def post_image_to_webp(sender, instance, **kwargs):
    if kwargs.get('update_fields') and 'image' not in (kwargs['update_fields'] or []):
        return
    from src.core.image_utils import convert_field_to_webp
    convert_field_to_webp(instance, 'image')
