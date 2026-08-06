"""Синхронізувати ієрархію категорій з YML Siker без повного wipe товарів."""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from src.catalog.siker_category_sync import sync_categories_and_products
from src.catalog.siker_yml import DEFAULT_EXPORT_URL, load_yml_bytes, parse_yml


class Command(BaseCommand):
    help = (
        'Оновлює дерево категорій з YML Siker, вирівнює під меню siker.ua, '
        'перепривʼязує товари за SKU, ховає Трактори/СТО.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--url', default=DEFAULT_EXPORT_URL)
        parser.add_argument('--file', default='', help='Локальний .yml замість URL')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Лише статистика YML, без запису',
        )

    def handle(self, *args, **options):
        file_path = (options['file'] or '').strip() or None
        self.stdout.write('Завантаження YML…')
        try:
            raw = load_yml_bytes(source=options['url'], file_path=file_path)
            catalog = parse_yml(raw)
        except Exception as exc:
            raise CommandError(f'Не вдалося прочитати YML: {exc}') from exc

        self.stdout.write(
            f'Категорій: {len(catalog.categories)}; товарів: {len(catalog.offers)}'
        )
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY-RUN: БД не змінено'))
            return

        stats = sync_categories_and_products(catalog.categories, catalog.offers)
        self.stdout.write(self.style.SUCCESS(
            f'Категорій upsert: {stats.categories_upserted}; '
            f'layout reparent: {stats.layout_reparented}; '
            f'приховано: {stats.categories_hidden}; '
            f'товарів перепривʼязано: {stats.products_remapped}; '
            f'пропуск offers: {stats.products_skipped}'
        ))
        from django.core.management import call_command
        call_command('assign_category_images')
