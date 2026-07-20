"""Оновлення цін товарів з прайсу Siker (рекомендована ціна)."""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from src.catalog.models import Product

DEFAULT_JSON = Path(settings.BASE_DIR) / 'data' / 'siker_recommended_prices.json'


class Command(BaseCommand):
    help = (
        'Ставить Product.price з рекомендованих цін Siker '
        '(data/siker_recommended_prices.json або --file).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default='',
            help='Шлях до JSON (sku → {price}) або до .xlsx прайсу',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показати зміни без запису',
        )

    def handle(self, *args, **options):
        path = Path((options['file'] or '').strip() or DEFAULT_JSON)
        if not path.is_file():
            raise CommandError(f'Файл не знайдено: {path}')

        prices = self._load_prices(path)
        if not prices:
            raise CommandError('У файлі немає цін')

        dry = options['dry_run']
        updated = missing = unchanged = 0
        for sku, new_price in sorted(prices.items()):
            product = Product.objects.filter(sku=sku).first()
            if product is None:
                missing += 1
                self.stdout.write(self.style.WARNING(f'немає товару sku={sku}'))
                continue
            if product.price == new_price:
                unchanged += 1
                continue
            self.stdout.write(
                f'{sku}: {product.price} → {new_price}  ({product.name[:50]})'
            )
            if not dry:
                product.price = new_price
                product.save(update_fields=['price', 'updated_at'])
            updated += 1

        label = 'DRY-RUN' if dry else 'Готово'
        self.stdout.write(self.style.SUCCESS(
            f'{label}: оновлено {updated}, без змін {unchanged}, '
            f'не знайдено {missing}, у файлі {len(prices)}.'
        ))

    def _load_prices(self, path: Path) -> dict[str, Decimal]:
        suffix = path.suffix.lower()
        if suffix == '.json':
            return self._from_json(path)
        if suffix in {'.xlsx', '.xlsm'}:
            return self._from_xlsx(path)
        raise CommandError('Підтримуються лише .json або .xlsx')

    def _from_json(self, path: Path) -> dict[str, Decimal]:
        raw = json.loads(path.read_text(encoding='utf-8'))
        result: dict[str, Decimal] = {}
        for sku, value in raw.items():
            if isinstance(value, dict):
                price_raw = value.get('price')
            else:
                price_raw = value
            result[str(sku).strip()] = self._decimal(price_raw)
        return result

    def _from_xlsx(self, path: Path) -> dict[str, Decimal]:
        try:
            import openpyxl
        except ImportError as exc:
            raise CommandError(
                'Для .xlsx потрібен openpyxl. Використайте data/siker_recommended_prices.json'
            ) from exc

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        rows = list(wb.active.iter_rows(values_only=True))
        wb.close()
        if not rows:
            return {}

        header = [str(c).strip() if c is not None else '' for c in rows[0]]
        try:
            sku_i = header.index('Код_товара')
            price_i = header.index('Цена рекомендова')
        except ValueError as exc:
            raise CommandError(
                'Очікувані колонки: Код_товара, Цена рекомендова'
            ) from exc

        result: dict[str, Decimal] = {}
        for row in rows[1:]:
            if not row or row[sku_i] is None:
                continue
            sku = str(row[sku_i]).strip()
            result[sku] = self._decimal(row[price_i])
        return result

    @staticmethod
    def _decimal(raw) -> Decimal:
        try:
            return Decimal(str(raw).strip().replace(',', '.'))
        except (InvalidOperation, AttributeError) as exc:
            raise CommandError(f'Некоректна ціна: {raw!r}') from exc
