import base64
import json
from decimal import Decimal
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from src.cart.services import CartService
from src.catalog.models import Category, Product
from src.orders.models import Order
from src.orders.services.liqpay import LiqPayService
from src.orders.services.pricing import price_cart
from src.orders.services.sync import sync_order_with_cart
from src.promotions.models import PromoCode

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(
    LIQPAY_PUBLIC_KEY='test_public',
    LIQPAY_PRIVATE_KEY='test_private',
    LIQPAY_SANDBOX=True,
    STORAGES=TEST_STORAGES,
)
class PricingConsistencyTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Price cat', is_active=True)
        self.factory = RequestFactory()

    def _product(self, sku, price, old_price=None):
        return Product.objects.create(
            category=self.category,
            name=f'Product {sku}',
            sku=sku,
            price=price,
            old_price=old_price,
            stock_quantity=10,
            is_active=True,
            is_on_sale=bool(old_price and old_price > price),
        )

    def _cart(self, items, promo_code=None, client=None):
        client = client or self.client
        session = client.session
        session['oyra_cart'] = {str(p.pk): qty for p, qty in items}
        if promo_code:
            session['promo_code'] = promo_code
        elif 'promo_code' in session:
            del session['promo_code']
        session.save()
        request = self.factory.get('/')
        request.session = client.session
        return CartService(request)

    def _liqpay_amount(self, order):
        data = LiqPayService().create_checkout(
            order,
            'https://example.com/ok',
            'https://example.com/cb',
        )
        payload = json.loads(base64.b64decode(data['data']).decode())
        return Decimal(str(payload['amount']))

    def test_sale_higher_than_base_unit_and_card(self):
        product = self._product(
            'HIGH-SALE',
            Decimal('1734.00'),
            Decimal('1574.00'),
        )
        cart = self._cart([(product, 1)])
        pricing = price_cart(cart, None)
        self.assertEqual(pricing.lines[0]['unit_price'], Decimal('1734.00'))
        self.assertEqual(pricing.total, Decimal('1734.00'))

        detail = self.client.get(product.get_absolute_url())
        self.assertContains(detail, '1 734,00')
        self.assertNotContains(detail, 'product-info__price-old')

        html = render_to_string('partials/product_card.html', {'product': product})
        self.assertNotIn('product-card__price-old', html)

    def test_sale_lower_than_base_shows_crossed(self):
        product = self._product(
            'LOW-SALE',
            Decimal('1574.00'),
            Decimal('1734.00'),
        )
        cart = self._cart([(product, 1)])
        pricing = price_cart(cart, None)
        self.assertEqual(pricing.lines[0]['unit_price'], Decimal('1574.00'))

        resp = self.client.get(product.get_absolute_url())
        self.assertContains(resp, 'product-info__price-old')
        self.assertContains(resp, '1 734,00')

    def test_no_promo_cart_order_liqpay_match(self):
        p1 = self._product('NP-1', Decimal('1734.00'))
        p2 = self._product('NP-2', Decimal('1574.00'))
        cart = self._cart([(p1, 1), (p2, 1)])
        pricing = price_cart(cart, None)
        self.assertEqual(pricing.total, Decimal('3308.00'))

        cart_page = self.client.get(reverse('cart:detail'))
        self.assertEqual(cart_page.context['total'], pricing.total)

        with patch('src.orders.views.notify_admins_after_checkout'):
            step1 = self.client.get(reverse('orders:checkout_step', kwargs={'step': 1}))
        order = Order.objects.get(pk=self.client.session['checkout_order_id'])
        self.assertEqual(order.subtotal, pricing.subtotal)
        self.assertEqual(order.discount, Decimal('0.00'))
        self.assertEqual(order.total, pricing.total)
        self.assertEqual(self._liqpay_amount(order), order.total)

    def test_promo_percent_rounding_cart_order_liqpay(self):
        p1 = self._product('PCT-1', Decimal('1574.00'))
        p2 = self._product('PCT-2', Decimal('1734.00'))
        promo = PromoCode.objects.create(
            code='OYRA15',
            discount_type=PromoCode.TYPE_PERCENT,
            discount_value=Decimal('15'),
            is_active=True,
        )
        cart = self._cart([(p1, 1), (p2, 1)], promo_code=promo.code)
        pricing = price_cart(cart, promo)
        self.assertEqual(pricing.subtotal, Decimal('3308.00'))
        self.assertEqual(pricing.discount, Decimal('496.20'))
        self.assertEqual(pricing.total, Decimal('2811.80'))

        cart_page = self.client.get(reverse('cart:detail'))
        self.assertEqual(cart_page.context['discount_amount'], pricing.discount)
        self.assertEqual(cart_page.context['total'], pricing.total)

        self.client.get(reverse('orders:checkout_step', kwargs={'step': 1}))
        order = Order.objects.get(pk=self.client.session['checkout_order_id'])
        self.assertEqual(order.discount, pricing.discount)
        self.assertEqual(order.total, pricing.total)
        self.assertEqual(self._liqpay_amount(order), Decimal('2811.80'))

    def test_promo_fixed_cart_order_liqpay(self):
        product = self._product('FIX-1', Decimal('2000.00'))
        promo = PromoCode.objects.create(
            code='MINUS100',
            discount_type=PromoCode.TYPE_FIXED,
            discount_value=Decimal('100.00'),
            is_active=True,
        )
        cart = self._cart([(product, 1)], promo_code=promo.code)
        pricing = price_cart(cart, promo)
        self.assertEqual(pricing.discount, Decimal('100.00'))
        self.assertEqual(pricing.total, Decimal('1900.00'))

        self.client.get(reverse('cart:detail'))
        self.client.get(reverse('orders:checkout_step', kwargs={'step': 1}))
        order = Order.objects.get(pk=self.client.session['checkout_order_id'])
        self.assertEqual(order.discount, pricing.discount)
        self.assertEqual(order.total, pricing.total)
        self.assertEqual(self._liqpay_amount(order), order.total)

    def test_price_change_resync_matches_cart(self):
        product = self._product('RESYNC-1', Decimal('1000.00'))
        cart = self._cart([(product, 2)])
        self.client.get(reverse('orders:checkout_step', kwargs={'step': 1}))
        order = Order.objects.get(pk=self.client.session['checkout_order_id'])
        self.assertEqual(order.total, Decimal('2000.00'))

        product.price = Decimal('1200.00')
        product.save(update_fields=['price', 'updated_at'])

        request = self.factory.get('/')
        request.session = self.client.session
        cart2 = CartService(request)
        ok = sync_order_with_cart(order, cart2, self.client.session)
        self.assertTrue(ok)
        order.refresh_from_db()
        pricing = price_cart(cart2, None)
        self.assertEqual(order.total, pricing.total)
        self.assertEqual(order.total, Decimal('2400.00'))
        self.assertEqual(self._liqpay_amount(order), Decimal('2400.00'))
