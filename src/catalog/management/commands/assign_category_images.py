"""Прив'язати існуючі файли media/categories/{slug}.webp до Category.image."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from src.catalog.models import Category


class Command(BaseCommand):
    help = (
        'Призначає кореневим категоріям зображення з media/categories/{slug}.webp '
        '(або .jpg/.png), якщо файл уже є в MEDIA_ROOT.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Лише показати, що буде зроблено',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        media_root = Path(settings.MEDIA_ROOT)
        categories_dir = media_root / 'categories'
        if not categories_dir.is_dir():
            self.stderr.write(self.style.ERROR(f'Немає директорії: {categories_dir}'))
            return

        roots = Category.objects.filter(parent__isnull=True, is_active=True).order_by('sort_order')
        assigned = 0
        missing = 0

        for cat in roots:
            found = None
            for ext in ('.webp', '.jpg', '.jpeg', '.png'):
                candidate = categories_dir / f'{cat.slug}{ext}'
                if candidate.is_file():
                    found = candidate
                    break

            if not found:
                missing += 1
                self.stdout.write(self.style.WARNING(f'немає файлу: {cat.slug}'))
                continue

            rel = f'categories/{found.name}'
            if dry_run:
                self.stdout.write(f'[dry-run] {cat.slug} ← {rel}')
                assigned += 1
                continue

            # Не викликаємо ImageField.save — файл уже на диску (уникаємо дубля + webp-циклу)
            if cat.image.name == rel:
                self.stdout.write(f'вже є: {cat.slug} → {rel}')
                assigned += 1
                continue

            Category.objects.filter(pk=cat.pk).update(image=rel)
            self.stdout.write(self.style.SUCCESS(f'OK {cat.slug} → {rel}'))
            assigned += 1

        self.stdout.write(
            self.style.NOTICE(f'Призначено: {assigned}, без файлу: {missing}')
        )
