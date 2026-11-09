from decimal import Decimal
from io import BytesIO
from xml.etree import ElementTree as ET

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from PIL import Image

from src.catalog.models import Brand, Category, Product, ProductImage
from src.seo.google_feed import (
    FALLBACK_CUSTOM_LABEL,
    G_NS,
    build_category_root_label_map,
    build_google_feed_xml,
)

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def _png(name='t.png') -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new('RGB', (8, 8), color=(20, 40, 60)).save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


@override_settings(STORAGES=TEST_STORAGES)
class GoogleFeedCustomLabelTests(TestCase):
    def setUp(self):
        self.root = Category.objects.create(
            name='Дім і сад', slug='dim-i-sad', is_active=True,
        )
        self.child = Category.objects.create(
            name='Садові павільйони, альтанки',
            slug='paviljony',
            parent=self.root,
            is_active=True,
        )
        self.other_root = Category.objects.create(
            name='Уцінений товар', slug='sale-root', is_active=True,
        )
        self.brand = Brand.objects.create(name='Atleto', slug='atleto')

        self.product_ok = Product.objects.create(
            category=self.child,
            brand=self.brand,
            name='Садовий павільйон Atleto',
            slug='paviljon-1',
            sku='FEED-1',
            price=Decimal('2500.00'),
            stock_quantity=3,
            is_active=True,
        )
        ProductImage.objects.create(
            product=self.product_ok, image=_png('a.png'), is_main=True,
        )

        self.product_other = Product.objects.create(
            category=self.other_root,
            brand=self.brand,
            name='Уцінений стілець',
            slug='sale-chair',
            sku='FEED-2',
            price=Decimal('500.00'),
            stock_quantity=1,
            is_active=True,
        )
        ProductImage.objects.create(
            product=self.product_other, image=_png('b.png'), is_main=True,
        )

    def test_root_label_map_walks_to_parent(self):
        labels = build_category_root_label_map()
        self.assertEqual(labels[self.child.pk], 'Дім і сад')
        self.assertEqual(labels[self.root.pk], 'Дім і сад')
        self.assertEqual(labels[self.other_root.pk], FALLBACK_CUSTOM_LABEL)

    def test_feed_contains_custom_label_0(self):
        request = RequestFactory().get('/feeds/google.xml')
        xml = build_google_feed_xml(request)
        root = ET.fromstring(xml)
        items = {
            el.findtext(f'{{{G_NS}}}id'): el.findtext(f'{{{G_NS}}}custom_label_0')
            for el in root.findall('./channel/item')
        }
        self.assertEqual(items['FEED-1'], 'Дім і сад')
        self.assertEqual(items['FEED-2'], FALLBACK_CUSTOM_LABEL)
        # product_type лишається листовою категорією
        item1 = next(
            el for el in root.findall('./channel/item')
            if el.findtext(f'{{{G_NS}}}id') == 'FEED-1'
        )
        self.assertEqual(
            item1.findtext(f'{{{G_NS}}}product_type'),
            'Садові павільйони, альтанки',
        )
