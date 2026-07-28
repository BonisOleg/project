from decimal import Decimal

from django.test import SimpleTestCase

from src.catalog.siker_yml import resolve_sale_prices


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

    def test_drop_higher_treated_as_old(self):
        price, old = resolve_sale_prices(Decimal('800'), Decimal('1000'))
        self.assertEqual(price, Decimal('800'))
        self.assertEqual(old, Decimal('1000'))
