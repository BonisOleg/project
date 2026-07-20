"""Виправлення unicode-слагів і прапорців для головної після імпорту Siker."""
from __future__ import annotations

from django.core.management.base import BaseCommand

from src.catalog.models import Brand, Category, Product, make_slug


class Command(BaseCommand):
    help = (
        'Перегенерує ASCII-слаги для товарів/категорій/брендів '
        'і виставляє is_new / is_top_sale для показу на головній.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--top',
            type=int,
            default=12,
            help='Скільки активних товарів позначити як топ продажу (за замовчуванням 12)',
        )

    def handle(self, *args, **options):
        top_n = max(0, options['top'])
        fixed_cats = self._fix_slugs(Category)
        fixed_brands = self._fix_slugs(Brand)
        fixed_products = self._fix_slugs(Product)

        active = list(
            Product.objects.active().order_by('-created_at', 'pk')
        )
        Product.objects.active().update(is_new=True, is_top_sale=False)
        top_ids = [p.pk for p in active[:top_n]]
        if top_ids:
            Product.objects.filter(pk__in=top_ids).update(is_top_sale=True)

        self.stdout.write(self.style.SUCCESS(
            f'Слаги: категорії {fixed_cats}, бренди {fixed_brands}, '
            f'товари {fixed_products}. Топ продажу: {len(top_ids)}.'
        ))

    def _fix_slugs(self, model) -> int:
        changed = 0
        for obj in model.objects.all().iterator():
            new_slug = make_slug(obj)
            if obj.slug != new_slug:
                obj.slug = new_slug
                obj.save(update_fields=['slug'])
                changed += 1
        return changed
