from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from src.catalog.models import Category, Product
from src.core.models import SiteSettings
from src.orders.analytics_purchase import build_purchase_datalayer
from src.orders.models import Order, OrderItem
from src.orders.services.ownership import make_order_access_token

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(STORAGES=TEST_STORAGES)
class PurchaseDataLayerTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Крісла', slug='krisla-root', is_active=True,
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Крісло тест',
            slug='krislo-test',
            sku='PUR-1',
            price=Decimal('1000.00'),
            stock_quantity=2,
            is_active=True,
        )
        self.order = Order.objects.create(
            first_name='Олена',
            last_name='Коваленко',
            phone='050 111-22-33',
            email='Buyer@Example.com',
            delivery_service=Order.DELIVERY_NP,
            delivery_city='Львів',
            delivery_address='Відділення 12',
            subtotal=Decimal('1000.00'),
            discount=Decimal('0'),
            total=Decimal('1000.00'),
            status=Order.STATUS_PENDING,
            payment_method=Order.PAYMENT_COD,
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            product_sku=self.product.sku,
            price=self.product.price,
            quantity=1,
            line_total=Decimal('1000.00'),
        )
        site = SiteSettings.get_solo()
        site.gtm_enabled = True
        site.gtm_container_id = 'GTM-TEST123'
        site.save()

    def test_build_purchase_payload(self):
        payload = build_purchase_datalayer(self.order)
        self.assertEqual(payload['event'], 'purchase')
        self.assertEqual(payload['ecommerce']['transaction_id'], self.order.order_number)
        self.assertEqual(payload['ecommerce']['currency'], 'UAH')
        self.assertEqual(payload['ecommerce']['value'], 1000.0)
        self.assertEqual(
            payload['ecommerce']['items'],
            [{
                'item_id': 'PUR-1',
                'item_name': 'Крісло тест',
                'price': 1000.0,
                'quantity': 1,
            }],
        )
        self.assertEqual(payload['user_data']['email'], 'buyer@example.com')
        self.assertEqual(payload['user_data']['phone_number'], '+380501112233')
        self.assertEqual(payload['user_data']['address']['first_name'], 'Олена')
        self.assertEqual(payload['user_data']['address']['city'], 'Львів')
        self.assertEqual(payload['user_data']['address']['country'], 'UA')

    def test_thank_you_embeds_json_script(self):
        token = make_order_access_token(self.order)
        url = reverse(
            'orders:thank_you',
            kwargs={'order_number': self.order.order_number},
        )
        response = self.client.get(url, {'t': token})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="oyra-purchase-datalayer"', content)
        self.assertIn('"event": "purchase"', content)
        self.assertIn(self.order.order_number, content)
        self.assertIn('purchase_datalayer.js', content)
