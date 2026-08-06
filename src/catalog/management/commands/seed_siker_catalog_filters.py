"""Замінити CatalogFilter на пріоритетний набір siker.ua."""

from django.core.management.base import BaseCommand
from django.db import transaction

from src.catalog.filters import siker_catalog_filter_definitions
from src.catalog.models import CatalogFilter


class Command(BaseCommand):
    help = 'Видаляє старі фільтри (Bonro) і створює Siker-набір: Ціна, Вид, Тип, Форма…'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Лише показати, що буде створено',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']
        defs = siker_catalog_filter_definitions()
        old_count = CatalogFilter.objects.count()
        if dry:
            self.stdout.write(f'[dry-run] видалити {old_count}, створити {len(defs)}:')
            for item in defs:
                self.stdout.write(
                    f'  {item.sort_order:3} {item.filter_type:10} {item.name}'
                    f' ← {item.attribute_name or "-"}'
                )
            return

        CatalogFilter.objects.all().delete()
        CatalogFilter.objects.bulk_create(defs)
        self.stdout.write(self.style.SUCCESS(
            f'OK: видалено {old_count}, створено {len(defs)} фільтрів Siker'
        ))
