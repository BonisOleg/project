from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Category, Product, ProductImage, make_slug


@receiver(pre_save, sender=Category)
def category_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = make_slug(instance)


@receiver(pre_save, sender=Product)
def product_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = make_slug(instance)


@receiver(post_save, sender=Category)
def category_image_to_webp(sender, instance, **kwargs):
    if kwargs.get('update_fields') and 'image' not in (kwargs['update_fields'] or []):
        return
    from src.core.image_utils import convert_field_to_webp
    convert_field_to_webp(instance, 'image')


@receiver(post_save, sender=ProductImage)
def product_image_to_webp(sender, instance, **kwargs):
    if kwargs.get('update_fields') and 'image' not in (kwargs['update_fields'] or []):
        return
    from src.core.image_utils import convert_field_to_webp
    convert_field_to_webp(instance, 'image')
