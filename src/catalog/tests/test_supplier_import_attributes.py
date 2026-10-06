"""Імпорт характеристик з вигрузки Prom (дубльовані колонки)."""
from __future__ import annotations

import io
from decimal import Decimal

from django.test import TestCase

from src.catalog.models import Category, Product, ProductAttribute, Supplier
from src.catalog.services.supplier_import import import_supplier_file
from src.catalog.services.supplier_import_parsers import parse_csv, parse_xlsx

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None


PROMO_HEADERS = [
    'Код_товара',
    'Название_позиции_укр',
    'Цена',
    'Наличие',
    'Название_группы',
    'Название_характеристики',
    'Измерение_Характеристики',
    'Значение_характеристики',
    'Название_характеристики_укр',
    'Значение_характеристики_укр',
    'Название_характеристики',
    'Измерение_Характеристики',
    'Значение_характеристики',
    'Название_характеристики_укр',
    'Значение_характеристики_укр',
]

PROMO_ROW = [
    '41300026',
    'Стіл обідній круглий Bonro В-957-600 Чорний',
    '2500',
    '3',
    'Меблі для дому',
    'Цвет',
    '',
    'Черный',
    'Колір',
    'Чорний',
    'Высота',
    'см',
    '75',
    'Висота',
    '75',
]


def _xlsx(rows: list[list[object]]) -> io.BytesIO:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buf = io.BytesIO()
    workbook.save(buf)
    buf.seek(0)
    return buf


def _csv_text(headers: list[str], row: list[object]) -> io.BytesIO:
    line = ','.join(headers) + '\n' + ','.join(str(c) for c in row) + '\n'
    return io.BytesIO(line.encode('utf-8'))


class SupplierImportAttributesTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name='Siker')
        self.category = Category.objects.create(name='Меблі для дому', is_active=True)

    def test_xlsx_keeps_duplicate_prom_param_columns(self):
        rows = parse_xlsx(_xlsx([PROMO_HEADERS, PROMO_ROW]), name_locale='uk')
        self.assertEqual(
            rows[0]['_attributes'],
            [('Колір', 'Чорний'), ('Висота', '75 см')],
        )

    def test_csv_keeps_duplicate_prom_param_columns(self):
        rows = parse_csv(_csv_text(PROMO_HEADERS, PROMO_ROW), name_locale='uk')
        self.assertEqual(
            rows[0]['_attributes'],
            [('Колір', 'Чорний'), ('Висота', '75 см')],
        )

    def test_import_creates_product_attributes(self):
        report = import_supplier_file(
            supplier=self.supplier,
            file_obj=_xlsx([PROMO_HEADERS, PROMO_ROW]),
            filename='export.xlsx',
            name_locale='uk',
        )
        self.assertEqual(report.created, 1)
        product = Product.objects.get(sku='41300026')
        attrs = list(product.attributes.order_by('sort_order').values_list('name', 'value'))
        self.assertEqual(attrs, [('Колір', 'Чорний'), ('Висота', '75 см')])

    def test_reimport_replaces_attributes(self):
        product = Product.objects.create(
            sku='41300026',
            name='Стіл',
            slug='stil-41300026',
            price=Decimal('1000.00'),
            category=self.category,
            stock_quantity=1,
        )
        ProductAttribute.objects.create(product=product, name='Стара', value='Так')

        import_supplier_file(
            supplier=self.supplier,
            file_obj=_xlsx([PROMO_HEADERS, PROMO_ROW]),
            filename='export.xlsx',
            name_locale='uk',
        )
        product.refresh_from_db()
        names = list(product.attributes.values_list('name', flat=True))
        self.assertEqual(names, ['Колір', 'Висота'])
        self.assertFalse(product.attributes.filter(name='Стара').exists())

    def test_file_without_params_keeps_existing_attributes(self):
        product = Product.objects.create(
            sku='41300026',
            name='Стіл',
            slug='stil-41300026',
            price=Decimal('1000.00'),
            category=self.category,
            stock_quantity=1,
        )
        ProductAttribute.objects.create(product=product, name='Колір', value='Чорний')

        header = 'Код_товара,Название_позиции_укр,Цена,Наличие,Название_группы'
        buf = io.BytesIO(
            f'{header}\n41300026,Стіл,2500,3,Меблі для дому\n'.encode('utf-8'),
        )
        import_supplier_file(
            supplier=self.supplier,
            file_obj=buf,
            filename='export.csv',
            name_locale='uk',
        )
        product.refresh_from_db()
        self.assertEqual(product.attributes.count(), 1)
        self.assertEqual(product.attributes.get().value, 'Чорний')
