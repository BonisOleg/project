"""Вирівняти дерево категорій під меню siker.ua (+ опційно sync з YML)."""
from django.core.cache import cache
from django.core.management.base import BaseCommand

from src.catalog.siker_category_sync import sync_categories_and_products
from src.catalog.siker_website_layout import apply_siker_website_layout
from src.catalog.siker_yml import DEFAULT_EXPORT_URL, load_yml_bytes, parse_yml
from src.catalog.signals import CATEGORIES_MENU_CACHE_KEY


class Command(BaseCommand):
    help = (
        'Перепривʼязує батьків категорій як на siker.ua '
        '(Дитячі товари, Крісла, Будівництво, Спорт…). '
        'За замовчуванням також тягне актуальний YML і товари.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--url', default=DEFAULT_EXPORT_URL)
        parser.add_argument(
            '--layout-only',
            action='store_true',
            help='Лише layout (без завантаження YML / remap SKU)',
        )

    def handle(self, *args, **options):
        if options['layout_only']:
            from src.catalog.siker_category_sync import deactivate_hidden_branches

            layout = apply_siker_website_layout()
            hidden = deactivate_hidden_branches()
            cache.delete(CATEGORIES_MENU_CACHE_KEY)
            self.stdout.write(self.style.SUCCESS(
                f'Layout OK: reparented={layout.reparented}, '
                f'renamed={layout.renamed}, synthetics={layout.synthetics}, '
                f'sorted={layout.sorted}, hidden={hidden}'
            ))
            from django.core.management import call_command
            call_command('assign_category_images')
            return

        url = options['url']
        self.stdout.write(f'Завантаження YML: {url}')
        raw = load_yml_bytes(url)
        if not raw:
            self.stderr.write(self.style.ERROR('Порожня відповідь YML'))
            return
        catalog = parse_yml(raw)
        self.stdout.write(
            f'Категорій: {len(catalog.categories)}; товарів: {len(catalog.offers)}'
        )
        stats = sync_categories_and_products(catalog.categories, catalog.offers)
        cache.delete(CATEGORIES_MENU_CACHE_KEY)
        self.stdout.write(self.style.SUCCESS(
            f'Upsert={stats.categories_upserted}; '
            f'layout_reparented={stats.layout_reparented}; '
            f'hidden={stats.categories_hidden}; '
            f'products_remapped={stats.products_remapped}'
        ))
        from django.core.management import call_command
        call_command('assign_category_images')
