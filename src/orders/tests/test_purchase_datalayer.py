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

    def test_value_excludes_delivery_and_applies_discount(self):
        self.order.subtotal = Decimal('1000.00')
        self.order.discount = Decimal('100.00')
        self.order.delivery_cost = Decimal('50.00')
        self.order.total = Decimal('950.00')
        self.order.save()
        payload = build_purchase_datalayer(self.order)
        self.assertEqual(payload['ecommerce']['value'], 900.0)

    def _thank_you(self, order):
        token = make_order_access_token(order)
        url = reverse('orders:thank_you', kwargs={'order_number': order.order_number})
        return self.client.get(url, {'t': token})

    def _poll(self, order, token=None):
        url = reverse('orders:purchase_status', kwargs={'order_number': order.order_number})
        if token is None:
            token = make_order_access_token(order)
        return self.client.get(url, {'t': token})

    def test_thank_you_embeds_json_script(self):
        response = self._thank_you(self.order)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="oyra-purchase-datalayer"', content)
        self.assertIn('"event": "purchase"', content)
        self.assertIn(self.order.order_number, content)
        self.assertIn('purchase_datalayer.js', content)

    def test_bank_transfer_embeds_purchase(self):
        self.order.payment_method = Order.PAYMENT_BANK
        self.order.status = Order.STATUS_AWAITING_PAYMENT
        self.order.save()
        content = self._thank_you(self.order).content.decode()
        self.assertIn('id="oyra-purchase-datalayer"', content)
        self.assertIn('"event": "purchase"', content)

    def test_liqpay_pending_polls_without_contacts(self):
        self.order.payment_method = Order.PAYMENT_LIQPAY
        self.order.status = Order.STATUS_PENDING
        self.order.save()
        page = self._thank_you(self.order)
        html = page.content.decode()
        self.assertNotIn('id="oyra-purchase-datalayer"', html)
        self.assertIn('id="oyra-purchase-poll"', html)

        pending = self._poll(self.order)
        self.assertEqual(pending.status_code, 200)
        self.assertIn('private, no-store', pending['Cache-Control'])
        body = pending.json()
        self.assertEqual(body, {'ready': False})
        self.assertNotIn('buyer@example.com', pending.content.decode())

        self.order.status = Order.STATUS_PAID
        self.order.save()
        paid = self._poll(self.order)
        self.assertEqual(paid.status_code, 200)
        self.assertIn('private, no-store', paid['Cache-Control'])
        payload = paid.json()['payload']
        self.assertEqual(payload['event'], 'purchase')
        self.assertEqual(payload['ecommerce']['value'], 1000.0)
        self.assertEqual(payload['user_data']['email'], 'buyer@example.com')

    def test_purchase_status_rejects_foreign_token(self):
        url = reverse(
            'orders:purchase_status',
            kwargs={'order_number': self.order.order_number},
        )
        response = self.client.get(url, {'t': 'not-a-valid-token'})
        self.assertEqual(response.status_code, 404)
