"""Прив'язати існуючі файли media/categories/{slug}.webp до Category.image."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from src.catalog.models import Category

# Після sync_siker slug стає name-externalId — шукаємо канонічний файл за назвою.
NAME_TO_IMAGE_STEM: dict[str, str] = {
    'дім і сад': 'dim-i-sad',
    'дорожні валізи': 'valizy',
    'дорожні сумки та валізи': 'valizy',
    'крісла': 'krisla',
    'будівництво і ремонт': 'budivnytstvo',
    'дитячі товари': 'dytiachi',
    'спорт і відпочинок': 'sport',
    'зоотовари': 'zootovary',
    'уцінений товар': 'utsineni',
    'трактори': 'traktory',
    'обладнання сто': 'sto',
    'обладнання для сто': 'sto',
}


def _stems_for_category(cat: Category) -> list[str]:
    stems: list[str] = []
    if cat.slug:
        stems.append(cat.slug)
        # krisla-23326849 → krisla
        if '-' in cat.slug:
            base, _, tail = cat.slug.rpartition('-')
            if tail.isdigit() and base:
                stems.append(base)
    name_key = (cat.name or '').strip().lower()
    alias = NAME_TO_IMAGE_STEM.get(name_key)
    if alias:
        stems.append(alias)
    # унікальні, порядок збережений
    seen: set[str] = set()
    out: list[str] = []
    for s in stems:
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _find_image(categories_dir: Path, cat: Category) -> Path | None:
    for stem in _stems_for_category(cat):
        for ext in ('.webp', '.jpg', '.jpeg', '.png'):
            candidate = categories_dir / f'{stem}{ext}'
            if candidate.is_file():
                return candidate
    return None


class Command(BaseCommand):
    help = (
        'Призначає кореневим категоріям зображення з media/categories/ '
        '(за slug, slug без external_id або канонічною назвою).'
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

        roots = Category.objects.filter(
            parent__isnull=True, is_active=True,
        ).order_by('sort_order')
        assigned = 0
        missing = 0

        for cat in roots:
            found = _find_image(categories_dir, cat)
            if not found:
                missing += 1
                self.stdout.write(self.style.WARNING(f'немає файлу: {cat.slug} ({cat.name})'))
                continue

            rel = f'categories/{found.name}'
            if dry_run:
                self.stdout.write(f'[dry-run] {cat.slug} ← {rel}')
                assigned += 1
                continue

            # Не викликаємо ImageField.save — файл уже на диску
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
