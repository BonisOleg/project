from decimal import Decimal
from io import BytesIO
from xml.etree import ElementTree as ET

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from PIL import Image

from src.catalog.models import Brand, Category, Product, ProductImage
import importlib

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
        self.assertEqual(item1.findtext(f'{{{G_NS}}}custom_label_1'), '2000-4999')
        self.assertEqual(item1.findtext(f'{{{G_NS}}}custom_label_2'), 'Всесезон')
        self.assertEqual(item1.findtext(f'{{{G_NS}}}custom_label_3'), 'Стандарт')


def _gtext(item, tag):
    return item.findtext(f'{{{G_NS}}}{tag}')


def _feed_item(sku):
    request = RequestFactory().get('/feeds/google.xml')
    root = ET.fromstring(build_google_feed_xml(request))
    for el in root.findall('./channel/item'):
        if el.findtext(f'{{{G_NS}}}id') == sku:
            return el
    raise AssertionError(sku)


@override_settings(STORAGES=TEST_STORAGES)
class GoogleFeedLabelRuleTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name='Narva', slug='narva')
        self.generators = Category.objects.create(
            name='Генератори', slug='generators', is_active=True, feed_season='winter',
        )
        self.inverter = Category.objects.create(
            name='Інверторні', slug='inverters', parent=self.generators, is_active=True,
        )
        self.winter_child_all = Category.objects.create(
            name='Аксесуари генераторів',
            slug='gen-acc',
            parent=self.generators,
            is_active=True,
            feed_season='all_season',
        )
        self.chairs = Category.objects.create(
            name='Крісла', slug='chairs-feed', is_active=True,
        )

    def _product(self, sku, name, price, category, **extra):
        product = Product.objects.create(
            category=category,
            brand=extra.pop('brand', self.brand),
            name=name,
            slug=sku.lower(),
            sku=sku,
            price=price,
            stock_quantity=1,
            is_active=True,
            **extra,
        )
        ProductImage.objects.create(product=product, image=_png(f'{sku}.png'), is_main=True)
        return product

    def test_price_groups_follow_selling_price(self):
        cases = (
            ('P799', Decimal('799.99'), 'до 799'),
            ('P800', Decimal('800.00'), '800-1999'),
            ('P1999', Decimal('1999.99'), '800-1999'),
            ('P2000', Decimal('2000.00'), '2000-4999'),
            ('P5000', Decimal('5000.00'), '5000+'),
        )
        for sku, price, label in cases:
            self._product(
                sku, f'Товар {sku}', price, self.chairs, old_price=Decimal('9000.00'),
            )
            item = _feed_item(sku)
            self.assertEqual(_gtext(item, 'custom_label_1'), label)
            self.assertEqual(_gtext(item, 'sale_price'), f'{price} UAH')

    def test_season_inherits_until_explicit_value(self):
        self._product('GEN-1', 'Генератор без коду', Decimal('6000'), self.inverter)
        item = _feed_item('GEN-1')
        self.assertEqual(_gtext(item, 'custom_label_2'), 'Зима')
        self.assertEqual(_gtext(item, 'custom_label_0'), 'Інше')

        self._product('ACC-1', 'Каністра', Decimal('300'), self.winter_child_all)
        all_season = _feed_item('ACC-1')
        self.assertEqual(_gtext(all_season, 'custom_label_2'), 'Всесезон')

        self._product('BAT-1', 'Батут дитячий 374', Decimal('7000'), self.winter_child_all)
        named = _feed_item('BAT-1')
        self.assertEqual(_gtext(named, 'custom_label_2'), 'Весна-літо')

        self._product('BAT-2', 'Батут узимку', Decimal('7000'), self.inverter)
        winter_name = _feed_item('BAT-2')
        self.assertEqual(_gtext(winter_name, 'custom_label_2'), 'Зима')

    def test_priority_auto_and_manual(self):
        self._product(
            'GEN-HIT', 'Генератор хіт', Decimal('6000'), self.inverter, is_top_sale=True,
        )
        self.assertEqual(_gtext(_feed_item('GEN-HIT'), 'custom_label_3'), 'Генератори')

        self._product(
            'CHAIR-HIT', 'Крісло хіт', Decimal('1500'), self.chairs, is_top_sale=True,
        )
        self.assertEqual(_gtext(_feed_item('CHAIR-HIT'), 'custom_label_3'), 'Хіт')

        self._product(
            'GEN-MAN', 'Генератор стандарт', Decimal('6000'), self.inverter,
            feed_priority='standard',
        )
        self.assertEqual(_gtext(_feed_item('GEN-MAN'), 'custom_label_3'), 'Стандарт')

    def test_mpn_only_for_single_code_with_brand(self):
        self._product(
            'NGI', 'Narva NGI-6500E - бензиновий інверторний генератор',
            Decimal('41999.98'), self.inverter,
        )
        item = _feed_item('NGI')
        self.assertEqual(_gtext(item, 'mpn'), 'NGI-6500E')
        self.assertIsNone(_gtext(item, 'identifier_exists'))

        self._product(
            'TWO', 'NGI-6500E та NGIO-6000E', Decimal('10000'), self.inverter,
        )
        two = _feed_item('TWO')
        self.assertIsNone(_gtext(two, 'mpn'))
        self.assertEqual(_gtext(two, 'identifier_exists'), 'no')

        self._product(
            'NOCODE', 'Генератор без моделі', Decimal('10000'), self.inverter,
        )
        plain = _feed_item('NOCODE')
        self.assertIsNone(_gtext(plain, 'mpn'))
        self.assertEqual(_gtext(plain, 'identifier_exists'), 'no')

        self._product(
            'NOBRAND', 'NGI-6500E без бренду', Decimal('10000'), self.inverter, brand=None,
        )
        naked = _feed_item('NOBRAND')
        self.assertIsNone(_gtext(naked, 'mpn'))
        self.assertEqual(_gtext(naked, 'identifier_exists'), 'no')

    def test_seed_updates_existing_category_names_only(self):
        known = Category.objects.create(name='Самокати', slug='scooters-seed', is_active=True)
        unknown = Category.objects.create(name='Сертифікат', slug='cert-seed', is_active=True)

        class _Apps:
            def get_model(self, app_label, model_name):
                self.seen = (app_label, model_name)
                return Category

        apps = _Apps()
        migration = importlib.import_module(
            'src.catalog.migrations.0012_google_feed_labels',
        )
        migration.seed_feed_seasons(apps, None)
        known.refresh_from_db()
        unknown.refresh_from_db()
        self.assertEqual(apps.seen, ('catalog', 'Category'))
        self.assertEqual(known.feed_season, 'spring_summer')
        self.assertEqual(unknown.feed_season, '')
