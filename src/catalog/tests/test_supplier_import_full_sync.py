"""Full Sync: upsert з файлу + деактивація SKU, яких немає у вигрузці."""

from __future__ import annotations

import io
from decimal import Decimal

from django.test import TestCase

from src.catalog.models import Category, Product, Supplier
from src.catalog.services.supplier_import import import_supplier_file
from src.catalog.services.supplier_import_parsers import SupplierImportParseError
from src.orders.models import Order, OrderItem

CSV_HEADER = (
    'Код_товара,Название_позиции_укр,Цена,Наличие,Название_группы'
)


def _csv(*lines: str) -> io.BytesIO:
    text = '\n'.join((CSV_HEADER, *lines)) + '\n'
    return io.BytesIO(text.encode('utf-8'))


class SupplierImportFullSyncTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name='Siker')
        self.other_supplier = Supplier.objects.create(name='Інший')
        self.category = Category.objects.create(name='Крісла геймерські', is_active=True)

    def _product(self, *, sku: str, **kwargs) -> Product:
        defaults = {
            'name': f'Товар {sku}',
            'slug': f'tovar-{sku}',
            'price': Decimal('1000.00'),
            'category': self.category,
            'supplier': self.supplier,
            'stock_quantity': 5,
            'is_active': True,
        }
        defaults.update(kwargs)
        return Product.objects.create(sku=sku, **defaults)

    def test_updates_price_and_zero_stock_and_keeps_active(self):
        product = self._product(sku='KEEP-1', price=Decimal('1999.00'), stock_quantity=8)

        report = import_supplier_file(
            supplier=self.supplier,
            file_obj=_csv('KEEP-1,Крісло оновлене,1500,0,Крісла геймерські'),
            filename='export.csv',
        )

        product.refresh_from_db()
        self.assertEqual(report.updated, 1)
        self.assertEqual(report.deactivated, 0)
        self.assertEqual(product.price, Decimal('1500.00'))
        self.assertEqual(product.stock_quantity, 0)
        self.assertTrue(product.is_active)
        self.assertEqual(product.availability, Product.AVAIL_OUT)

    def test_deactivates_products_missing_from_file(self):
        kept = self._product(sku='KEEP-1')
        other = self._product(
            sku='OTHER-1',
            slug='tovar-other-1',
            supplier=self.other_supplier,
        )
        manual = self._product(
            sku='MANUAL-1',
            slug='tovar-manual-1',
            supplier=None,
        )

        report = import_supplier_file(
            supplier=self.supplier,
            file_obj=_csv('KEEP-1,Крісло,1200,3,Крісла геймерські'),
            filename='export.csv',
        )

        kept.refresh_from_db()
        other.refresh_from_db()
        manual.refresh_from_db()

        self.assertEqual(report.updated, 1)
        self.assertEqual(report.deactivated, 2)
        self.assertTrue(kept.is_active)
        self.assertEqual(kept.stock_quantity, 3)

        for missing in (other, manual):
            self.assertFalse(missing.is_active)
            self.assertEqual(missing.stock_quantity, 0)
            self.assertEqual(missing.availability, Product.AVAIL_OUT)
            self.assertTrue(Product.objects.filter(pk=missing.pk).exists())

    def test_reactivates_previously_deactivated_sku(self):
        product = self._product(
            sku='BACK-1',
            is_active=False,
            stock_quantity=0,
        )

        report = import_supplier_file(
            supplier=self.supplier,
            file_obj=_csv('BACK-1,Крісло знову,2100,4,Крісла геймерські'),
            filename='export.csv',
        )

        product.refresh_from_db()
        self.assertEqual(report.updated, 1)
        self.assertTrue(product.is_active)
        self.assertEqual(product.stock_quantity, 4)
        self.assertEqual(product.availability, Product.AVAIL_IN_STOCK)

    def test_file_without_sku_does_not_change_catalog(self):
        product = self._product(sku='KEEP-1', stock_quantity=9)

        report = import_supplier_file(
            supplier=self.supplier,
            file_obj=_csv(',Крісло без коду,1000,5,Крісла геймерські'),
            filename='export.csv',
        )

        product.refresh_from_db()
        self.assertEqual(report.created, 0)
        self.assertEqual(report.updated, 0)
        self.assertEqual(report.deactivated, 0)
        self.assertTrue(report.error_count >= 1)
        self.assertTrue(product.is_active)
        self.assertEqual(product.stock_quantity, 9)

    def test_header_only_file_raises_and_leaves_catalog(self):
        product = self._product(sku='KEEP-1')
        buf = io.BytesIO((CSV_HEADER + '\n').encode('utf-8'))

        with self.assertRaises(SupplierImportParseError):
            import_supplier_file(
                supplier=self.supplier,
                file_obj=buf,
                filename='export.csv',
            )

        product.refresh_from_db()
        self.assertTrue(product.is_active)
        self.assertEqual(product.stock_quantity, 5)

    def test_order_item_protect_does_not_block_deactivation(self):
        ordered = self._product(sku='ORDERED-1')
        kept = self._product(sku='KEEP-1', slug='tovar-keep-1')
        order = Order.objects.create(
            first_name='Іван',
            last_name='Тест',
            phone='+380501112233',
            email='t@example.com',
            delivery_service=Order.DELIVERY_NP,
            delivery_city='Київ',
            delivery_address='Відділення 1',
            subtotal='1000.00',
            total='1000.00',
        )
        OrderItem.objects.create(
            order=order,
            product=ordered,
            product_name=ordered.name,
            product_sku=ordered.sku,
            price=ordered.price,
            quantity=1,
            line_total=ordered.price,
        )

        report = import_supplier_file(
            supplier=self.supplier,
            file_obj=_csv('KEEP-1,Крісло,1200,2,Крісла геймерські'),
            filename='export.csv',
        )

        ordered.refresh_from_db()
        kept.refresh_from_db()
        self.assertEqual(report.deactivated, 1)
        self.assertFalse(ordered.is_active)
        self.assertEqual(ordered.stock_quantity, 0)
        self.assertTrue(Product.objects.filter(pk=ordered.pk).exists())
        self.assertEqual(OrderItem.objects.filter(product=ordered).count(), 1)
        self.assertTrue(kept.is_active)

    def test_invalid_row_sku_is_not_deactivated(self):
        """Бита ціна в файлі: товар не оновлюється і не знімається з продажу."""
        broken = self._product(sku='BROKEN-1', price=Decimal('500.00'), stock_quantity=7)
        extra = self._product(sku='EXTRA-1', slug='tovar-extra-1')

        report = import_supplier_file(
            supplier=self.supplier,
            file_obj=_csv(
                'BROKEN-1,Крісло,не-ціна,3,Крісла геймерські',
                'KEEP-NEW,Нове крісло,800,1,Крісла геймерські',
            ),
            filename='export.csv',
        )

        broken.refresh_from_db()
        extra.refresh_from_db()
        self.assertEqual(report.created, 1)
        self.assertTrue(report.error_count >= 1)
        self.assertTrue(broken.is_active)
        self.assertEqual(broken.price, Decimal('500.00'))
        self.assertEqual(broken.stock_quantity, 7)
        self.assertFalse(extra.is_active)
        self.assertTrue(Product.objects.filter(sku='KEEP-NEW').exists())
