"""
Регрес на баг: ручний імпорт XLSX ігнорував колонку «Ссылка_изображения»,
тому товари створювались/оновлювались без жодного фото, хоча посилання
в вигрузці Prom/Siker були коректні (напр. sku 42300046).
"""
from __future__ import annotations

import io
from unittest.mock import patch

from django.test import TestCase

from src.catalog.models import Category, Product, ProductImage, Supplier
from src.catalog.services.supplier_import import import_supplier_file
from src.catalog.services.supplier_import_parsers import parse_xlsx

try:
    import openpyxl
except ImportError:  # pragma: no cover - openpyxl завжди є в цьому проєкті
    openpyxl = None


def _build_xlsx(rows: list[list[object]]) -> io.BytesIO:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buf = io.BytesIO()
    workbook.save(buf)
    buf.seek(0)
    return buf


HEADER = [
    'Код_товара',
    'Название_позиции_укр',
    'Цена',
    'Наличие',
    'Название_группы',
    'Ссылка_изображения',
]

FAKE_IMAGE_BYTES = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
    b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
    b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
)


class SupplierImportImageBackfillTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name='Siker')
        self.category = Category.objects.create(name='Крісла геймерські', is_active=True)

    def _download_image_stub(self, url: str):
        return FAKE_IMAGE_BYTES, url.rsplit('/', 1)[-1]

    def test_xlsx_parser_extracts_image_urls_column(self):
        buf = _build_xlsx([
            HEADER,
            [
                '42300046',
                'Крісло геймерське Bonro B-810',
                '2811',
                '10',
                'Крісла геймерські',
                'https://cdn.example/a.jpg, https://cdn.example/b.jpg',
            ],
        ])
        rows = parse_xlsx(buf, name_locale='uk')
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]['images'],
            'https://cdn.example/a.jpg, https://cdn.example/b.jpg',
        )

    def test_new_product_downloads_images_from_url_column(self):
        buf = _build_xlsx([
            HEADER,
            [
                '42300046',
                'Крісло геймерське Bonro B-810',
                '2811',
                '10',
                'Крісла геймерські',
                'https://cdn.example/a.jpg, https://cdn.example/b.jpg',
            ],
        ])
        with patch(
            'src.catalog.services.supplier_import.download_image',
            side_effect=self._download_image_stub,
        ):
            report = import_supplier_file(
                supplier=self.supplier,
                file_obj=buf,
                filename='export.xlsx',
                name_locale='uk',
            )

        self.assertEqual(report.created, 1)
        self.assertEqual(report.images_added, 2)
        product = Product.objects.get(sku='42300046')
        self.assertEqual(product.images.count(), 2)
        self.assertTrue(product.images.filter(is_main=True).exists())

    def test_existing_gallery_is_not_touched_on_reimport(self):
        product = Product.objects.create(
            sku='42300046',
            name='Крісло',
            slug='kryslo-42300046',
            price='2811.00',
            category=self.category,
            stock_quantity=5,
        )
        ProductImage.objects.create(product=product, image='products/existing.jpg', is_main=True)

        buf = _build_xlsx([
            HEADER,
            [
                '42300046',
                'Крісло геймерське Bonro B-810',
                '2900',
                '8',
                'Крісла геймерські',
                'https://cdn.example/a.jpg',
            ],
        ])
        with patch(
            'src.catalog.services.supplier_import.download_image',
        ) as mocked:
            report = import_supplier_file(
                supplier=self.supplier,
                file_obj=buf,
                filename='export.xlsx',
                name_locale='uk',
            )
            mocked.assert_not_called()

        self.assertEqual(report.updated, 1)
        self.assertEqual(report.images_added, 0)
        product.refresh_from_db()
        self.assertEqual(product.images.count(), 1)

    def test_broken_image_link_does_not_fail_import(self):
        buf = _build_xlsx([
            HEADER,
            [
                '42300046',
                'Крісло геймерське Bonro B-810',
                '2811',
                '10',
                'Крісла геймерські',
                'https://cdn.example/broken.jpg',
            ],
        ])
        with patch(
            'src.catalog.services.supplier_import.download_image',
            side_effect=TimeoutError('no response'),
        ):
            report = import_supplier_file(
                supplier=self.supplier,
                file_obj=buf,
                filename='export.xlsx',
                name_locale='uk',
            )

        self.assertEqual(report.created, 1)
        self.assertEqual(report.images_added, 0)
        self.assertEqual(report.images_failed, 1)
        product = Product.objects.get(sku='42300046')
        self.assertEqual(product.images.count(), 0)
