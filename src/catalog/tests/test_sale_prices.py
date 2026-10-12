import json
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from src.catalog.models import Category, Product
from src.catalog.siker_yml import resolve_sale_prices

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


class ResolveSalePricesTests(SimpleTestCase):
    def test_price_drop_lower_becomes_current(self):
        price, old = resolve_sale_prices(Decimal('1000'), Decimal('800'))
        self.assertEqual(price, Decimal('800'))
        self.assertEqual(old, Decimal('1000'))

    def test_no_drop(self):
        price, old = resolve_sale_prices(Decimal('1000'), None)
        self.assertEqual(price, Decimal('1000'))
        self.assertIsNone(old)

    def test_drop_equals_price(self):
        price, old = resolve_sale_prices(Decimal('1000'), Decimal('1000'))
        self.assertEqual(price, Decimal('1000'))
        self.assertIsNone(old)

    def test_drop_higher_uses_drop_as_selling(self):
        price, old = resolve_sale_prices(Decimal('800'), Decimal('1000'))
        self.assertEqual(price, Decimal('1000'))
        self.assertIsNone(old)


@override_settings(STORAGES=TEST_STORAGES)
class UpdateSikerPricesClearsOldTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Sale cat', is_active=True)
        self.product = Product.objects.create(
            category=self.category,
            name='Sale product',
            sku='SIKER-UPD-1',
            price=Decimal('1500.00'),
            old_price=Decimal('1400.00'),
            stock_quantity=5,
            is_active=True,
            is_on_sale=True,
        )

    def test_update_clears_stale_old_price(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'prices.json'
            path.write_text(
                json.dumps({'SIKER-UPD-1': {'price': '1600.00'}}),
                encoding='utf-8',
            )
            call_command('update_siker_prices', file=str(path))
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal('1600.00'))
        self.assertIsNone(self.product.old_price)
        self.assertFalse(self.product.is_on_sale)


@override_settings(STORAGES=TEST_STORAGES)
class FixSalePricesNoSwapTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Fix cat', is_active=True)
        self.product = Product.objects.create(
            category=self.category,
            name='Inverted old',
            sku='FIX-SALE-1',
            price=Decimal('1734.00'),
            old_price=Decimal('1574.00'),
            stock_quantity=3,
            is_active=True,
            is_on_sale=True,
        )

    def test_fix_clears_invalid_old_without_swap(self):
        call_command('fix_sale_prices', skip_delete_seed=True)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal('1734.00'))
        self.assertIsNone(self.product.old_price)
        self.assertFalse(self.product.is_on_sale)

    def test_dry_run_does_not_write(self):
        call_command('fix_sale_prices', dry_run=True, skip_delete_seed=True)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal('1734.00'))
        self.assertEqual(self.product.old_price, Decimal('1574.00'))
