"""Виправлення інвертованих акційних цін і видалення seed-тестових товарів."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from src.catalog.models import Product

# SKU з seed_data.SAMPLE_PRODUCTS
SEED_SKUS = (
    'G9040',
    'P9040',
    'B619',
    'B173',
    'BAT374',
    'SP2002',
    'B016',
    'VAL28',
)


class Command(BaseCommand):
    help = (
        'Міняє місцями price/old_price, де old_price < price (помилка імпорту Siker), '
        'оновлює is_on_sale, опційно видаляє seed-тестові товари.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Лише показати зміни',
        )
        parser.add_argument(
            '--skip-delete-seed',
            action='store_true',
            help='Не видаляти тестові seed-товари',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']
        skip_delete = options['skip_delete_seed']

        inverted = Product.objects.filter(
            old_price__isnull=False,
            old_price__lt=F('price'),
        )
        count = inverted.count()
        self.stdout.write(f'Інвертованих цін: {count}')

        if dry:
            for p in inverted[:10]:
                self.stdout.write(
                    f'  {p.sku}: price {p.price} ↔ old {p.old_price}'
                )
            if count > 10:
                self.stdout.write(f'  … ще {count - 10}')
        else:
            # bulk swap через два кроки з тимчасовим полем неможливий без raw SQL;
            # оновлюємо пакетами в Python (сотні записів — ок).
            swapped = 0
            for p in inverted.iterator(chunk_size=200):
                new_price, new_old = p.old_price, p.price
                p.price = new_price
                p.old_price = new_old
                p.is_on_sale = True
                p.save(update_fields=['price', 'old_price', 'is_on_sale', 'updated_at'])
                swapped += 1
            self.stdout.write(self.style.SUCCESS(f'Поміняно цін: {swapped}'))

            # Синхронізація прапорця для всіх з коректною акцією
            synced = Product.objects.filter(
                old_price__isnull=False,
                old_price__gt=F('price'),
            ).update(is_on_sale=True)
            cleared = Product.objects.filter(
                is_on_sale=True,
            ).filter(
                old_price__isnull=True,
            ).update(is_on_sale=False)
            self.stdout.write(f'is_on_sale=True: {synced}, знято зайві: {cleared}')

        seed_qs = Product.objects.filter(sku__in=SEED_SKUS)
        seed_count = seed_qs.count()
        if skip_delete:
            self.stdout.write(f'Seed-товарів залишено: {seed_count}')
            return

        if dry:
            for p in seed_qs:
                self.stdout.write(f'  DELETE {p.sku} — {p.name[:50]}')
            self.stdout.write(self.style.WARNING(f'DRY-RUN: видалити б {seed_count} seed'))
            return

        deleted, details = seed_qs.delete()
        self.stdout.write(self.style.SUCCESS(
            f'Видалено seed: {deleted} обʼєктів ({details})'
        ))

        from django.db.models import F as F2
        on_sale = Product.objects.active().filter(
            old_price__isnull=False,
            old_price__gt=F2('price'),
        ).count()
        self.stdout.write(self.style.SUCCESS(f'Зараз в «Акціях»: {on_sale} товарів'))
