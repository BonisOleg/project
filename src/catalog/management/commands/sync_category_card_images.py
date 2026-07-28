"""Синхронізація фото кореневих категорій на дублікати та нащадків."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from src.catalog.models import Category


class Command(BaseCommand):
    help = (
        'Копіює Category.image з коренів, що мають фото, на одноіменні корені-дублікати '
        'і на всіх нащадків без власного фото. Репарентить дітей з «порожніх» коренів '
        'на корінь з фото.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']
        roots_with_image = list(
            Category.objects.filter(parent__isnull=True)
            .exclude(image='')
            .exclude(image__isnull=True)
        )
        by_name: dict[str, Category] = {}
        for root in roots_with_image:
            # пріоритет активним
            prev = by_name.get(root.name)
            if prev is None or (root.is_active and not prev.is_active):
                by_name[root.name] = root

        copied_roots = 0
        reparented = 0
        copied_desc = 0

        for name, donor in by_name.items():
            twins = Category.objects.filter(parent__isnull=True, name=name).exclude(pk=donor.pk)
            for twin in twins:
                if not getattr(twin.image, 'name', None):
                    self.stdout.write(f'root image {twin.slug} ← {donor.slug}')
                    if not dry:
                        Category.objects.filter(pk=twin.pk).update(image=donor.image.name)
                    copied_roots += 1
                kids = Category.objects.filter(parent=twin)
                n = kids.count()
                if n:
                    self.stdout.write(f'reparent {n} kids: {twin.slug} → {donor.slug}')
                    if not dry:
                        kids.update(parent=donor)
                    reparented += n

        # Нащадки без фото ← фото кореня гілки
        for donor in by_name.values():
            ids = donor.get_descendant_ids()
            descendants = Category.objects.filter(pk__in=ids).exclude(pk=donor.pk).filter(
                Q(image='') | Q(image__isnull=True)
            )
            n = descendants.count()
            if n:
                self.stdout.write(f'descendants {n} ← {donor.slug}')
                if not dry:
                    descendants.update(image=donor.image.name)
                copied_desc += n

        label = 'DRY-RUN' if dry else 'Готово'
        self.stdout.write(self.style.SUCCESS(
            f'{label}: коренів-дублів {copied_roots}, '
            f'reparent {reparented}, нащадків {copied_desc}'
        ))
