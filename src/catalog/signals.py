from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Category, Product, make_slug


@receiver(pre_save, sender=Category)
def category_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = make_slug(instance)


@receiver(pre_save, sender=Product)
def product_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = make_slug(instance)
