import base64
import hashlib
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import signing
from django.test import TestCase, override_settings
from django.urls import reverse

from src.catalog.models import Category, Product
from src.orders.models import Order, OrderItem
from src.orders.services.ownership import (
    make_order_access_token,
    remember_own_order,
    verify_order_access_token,
)
from src.orders.services.promo_usage import mark_promo_used
from src.orders.services.sync import sync_order_with_cart
from src.promotions.models import PromoCode

User = get_user_model()

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
class PromoFixBase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Промо кат', is_active=True)
        self.product = Product.objects.create(
            category=self.category,
            name='Промо товар',
            sku='PROMO-ORD-1',
            price=Decimal('1000.00'),
            stock_quantity=20,
            is_active=True,
        )
        self.promo = PromoCode.objects.create(
            code='SAVE15',
            discount_type=PromoCode.TYPE_PERCENT,
            discount_value=Decimal('15'),
            is_active=True,
        )

    def _session_cart(self, qty=1, promo=None, client=None):
        client = client or self.client
        session = client.session
        session['oyra_cart'] = {str(self.product.pk): qty}
        if promo:
            session['promo_code'] = promo
        elif 'promo_code' in session:
            del session['promo_code']
        session.save()

    def _make_order(self, *, discount=Decimal('150'), promo_code='SAVE15', user=None, qty=1):
        subtotal = self.product.price * qty
        order = Order.objects.create(
            user=user,
            first_name='Іван',
            last_name='Тест',
            phone='+380501112233',
            email='buyer@example.com',
            delivery_service=Order.DELIVERY_NP,
            delivery_city='Київ',
            delivery_address='Відділення 1',
            subtotal=subtotal,
            discount=discount,
            total=subtotal - discount,
            promo_code=promo_code,
            status=Order.STATUS_PENDING,
            liqpay_order_id='liqpay-test-001',
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            product_sku=self.product.sku,
            price=self.product.price,
            quantity=qty,
            line_total=subtotal,
        )
        return order

    def _cart_service(self, client=None):
        from django.test import RequestFactory
        from src.cart.services import CartService

        client = client or self.client
        request = RequestFactory().get('/')
        request.session = client.session
        return CartService(request)

    def _liqpay_callback_payload(self, order, status='success'):
        payload = {
            'order_id': order.liqpay_order_id,
            'status': status,
            'transaction_id': 'tx-1',
        }
        data_b64 = base64.b64encode(
            json.dumps(payload, ensure_ascii=False).encode(),
        ).decode()
        raw = ('test_private' + data_b64 + 'test_private').encode()
        signature = base64.b64encode(hashlib.sha1(raw).digest()).decode()
        return data_b64, signature


class SyncBeforePaymentTests(PromoFixBase):
    def test_stale_promo_cleared_before_payment(self):
        self._session_cart(promo='SAVE15')
        self.client.get(reverse('orders:checkout'))
        order = Order.objects.get()
        self.assertEqual(order.discount, Decimal('150.00'))
        self.assertEqual(order.promo_code, 'SAVE15')

        session = self.client.session
        session.pop('promo_code', None)
        session.save()

        resp = self.client.post(
            reverse('orders:checkout_step', kwargs={'step': 4}),
            {'payment_method': Order.PAYMENT_COD},
        )
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.discount, Decimal('0'))
        self.assertEqual(order.promo_code, '')
        self.assertEqual(order.total, order.subtotal)

    def test_invalid_session_promo_cleared_on_sync(self):
        order = self._make_order()
        self._session_cart(promo='SAVE15')
        session = self.client.session
        session['checkout_order_id'] = order.pk
        session.save()

        self.promo.is_active = False
        self.promo.save(update_fields=['is_active'])

        session = self.client.session
        cart = self._cart_service()
        ok = sync_order_with_cart(order, cart, session)
        session.save()
        self.assertTrue(ok)
        order.refresh_from_db()
        self.assertEqual(order.discount, Decimal('0'))
        self.assertEqual(order.promo_code, '')
        self.assertNotIn('promo_code', self.client.session)

    def test_cart_change_updates_items_before_payment(self):
        self._session_cart(qty=1, promo='SAVE15')
        self.client.get(reverse('orders:checkout'))
        order = Order.objects.get()
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.subtotal, Decimal('1000.00'))

        session = self.client.session
        session['oyra_cart'] = {str(self.product.pk): 3}
        session.save()

        resp = self.client.post(
            reverse('orders:checkout_step', kwargs={'step': 4}),
            {'payment_method': Order.PAYMENT_BANK},
        )
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.items.get().quantity, 3)
        self.assertEqual(order.subtotal, Decimal('3000.00'))
        self.assertEqual(order.discount, Decimal('450.00'))
        self.assertEqual(order.total, Decimal('2550.00'))

    def test_no_promo_in_session_discount_zero(self):
        self._session_cart()
        self.client.get(reverse('orders:checkout'))
        order = Order.objects.get()
        self.assertEqual(order.discount, Decimal('0'))
        self.assertEqual(order.promo_code, '')

        resp = self.client.post(
            reverse('orders:checkout_step', kwargs={'step': 4}),
            {'payment_method': Order.PAYMENT_COD},
        )
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.discount, Decimal('0'))
        self.assertEqual(order.total, order.subtotal)


class MaxUsesAndCountingTests(PromoFixBase):
    def test_max_uses_reached_is_invalid(self):
        self.promo.max_uses = 1
        self.promo.used_count = 1
        self.promo.save(update_fields=['max_uses', 'used_count'])
        self.assertFalse(self.promo.is_valid())

        order = self._make_order()
        self._session_cart(promo='SAVE15')
        session = self.client.session
        session['checkout_order_id'] = order.pk
        session.save()

        ok = sync_order_with_cart(order, self._cart_service(), self.client.session)
        self.assertTrue(ok)
        order.refresh_from_db()
        self.assertEqual(order.discount, Decimal('0'))
        self.assertEqual(order.promo_code, '')

    def test_cod_increments_used_count_once(self):
        self._session_cart(promo='SAVE15')
        self.client.get(reverse('orders:checkout'))
        self.client.post(
            reverse('orders:checkout_step', kwargs={'step': 4}),
            {'payment_method': Order.PAYMENT_COD},
        )
        self.promo.refresh_from_db()
        order = Order.objects.get()
        self.assertEqual(self.promo.used_count, 1)
        self.assertTrue(order.promo_counted)

        mark_promo_used(order)
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.used_count, 1)

    def test_liqpay_callback_idempotent(self):
        order = self._make_order()
        self.assertEqual(self.promo.used_count, 0)

        data, signature = self._liqpay_callback_payload(order)
        url = reverse('orders:liqpay_callback')
        r1 = self.client.post(url, {'data': data, 'signature': signature})
        self.assertEqual(r1.status_code, 200)
        self.promo.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertEqual(self.promo.used_count, 1)
        self.assertTrue(order.promo_counted)

        r2 = self.client.post(url, {'data': data, 'signature': signature})
        self.assertEqual(r2.status_code, 200)
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.used_count, 1)


class OwnerCheckTests(PromoFixBase):
    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(
            email='owner@example.com', password='pass12345',
        )
        self.other = User.objects.create_user(
            email='other@example.com', password='pass12345',
        )
        self.order = self._make_order(user=self.owner, discount=Decimal('0'), promo_code='')

    def test_other_user_gets_404_on_thank_you_and_retry(self):
        self.client.login(email='other@example.com', password='pass12345')
        r1 = self.client.get(
            reverse('orders:thank_you', kwargs={'order_number': self.order.order_number}),
        )
        self.assertEqual(r1.status_code, 404)
        r2 = self.client.get(
            reverse('orders:retry_payment', kwargs={'order_number': self.order.order_number}),
        )
        self.assertEqual(r2.status_code, 404)

    def test_anonymous_without_own_orders_404(self):
        r1 = self.client.get(
            reverse('orders:thank_you', kwargs={'order_number': self.order.order_number}),
        )
        self.assertEqual(r1.status_code, 404)
        r2 = self.client.get(
            reverse('orders:retry_payment', kwargs={'order_number': self.order.order_number}),
        )
        self.assertEqual(r2.status_code, 404)

    def test_owner_ok(self):
        self.client.login(email='owner@example.com', password='pass12345')
        r1 = self.client.get(
            reverse('orders:thank_you', kwargs={'order_number': self.order.order_number}),
        )
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.get(
            reverse('orders:retry_payment', kwargs={'order_number': self.order.order_number}),
        )
        self.assertEqual(r2.status_code, 302)
        self.assertEqual(self.client.session.get('checkout_order_id'), self.order.pk)

    def test_guest_with_own_orders_ok(self):
        guest_order = self._make_order(
            user=None, discount=Decimal('0'), promo_code='', qty=1,
        )
        guest_order.liqpay_order_id = 'liqpay-guest-1'
        guest_order.save(update_fields=['liqpay_order_id'])

        session = self.client.session
        remember_own_order(session, guest_order)
        session.save()

        r1 = self.client.get(
            reverse('orders:thank_you', kwargs={'order_number': guest_order.order_number}),
        )
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.get(
            reverse('orders:retry_payment', kwargs={'order_number': guest_order.order_number}),
        )
        self.assertEqual(r2.status_code, 302)

    def test_retry_does_not_set_foreign_order_in_session(self):
        self.client.login(email='other@example.com', password='pass12345')
        before = self.client.session.get('checkout_order_id')
        self.client.get(
            reverse('orders:retry_payment', kwargs={'order_number': self.order.order_number}),
        )
        self.assertEqual(self.client.session.get('checkout_order_id'), before)


@override_settings(
    LIQPAY_PUBLIC_KEY='test_public',
    LIQPAY_PRIVATE_KEY='test_private',
    LIQPAY_SANDBOX=True,
    STORAGES=TEST_STORAGES,
)
class OrderAccessTokenTests(PromoFixBase):
    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(
            email='token-owner@example.com', password='pass12345',
        )
        self.order = self._make_order(
            user=self.owner, discount=Decimal('0'), promo_code='',
        )

    def test_thank_you_valid_token_no_session_200(self):
        token = make_order_access_token(self.order)
        url = reverse(
            'orders:thank_you',
            kwargs={'order_number': self.order.order_number},
        )
        resp = self.client.get(url, {'t': token})
        self.assertEqual(resp.status_code, 200)

    def test_thank_you_tampered_token_404(self):
        token = make_order_access_token(self.order) + 'x'
        url = reverse(
            'orders:thank_you',
            kwargs={'order_number': self.order.order_number},
        )
        resp = self.client.get(url, {'t': token})
        self.assertEqual(resp.status_code, 404)

    def test_thank_you_other_order_token_404(self):
        other = self._make_order(
            user=None, discount=Decimal('0'), promo_code='', qty=1,
        )
        other.liqpay_order_id = 'liqpay-other-tok'
        other.save(update_fields=['liqpay_order_id'])
        token = make_order_access_token(other)
        url = reverse(
            'orders:thank_you',
            kwargs={'order_number': self.order.order_number},
        )
        resp = self.client.get(url, {'t': token})
        self.assertEqual(resp.status_code, 404)

    def test_thank_you_expired_token_404(self):
        token = make_order_access_token(self.order)
        url = reverse(
            'orders:thank_you',
            kwargs={'order_number': self.order.order_number},
        )
        with patch(
            'src.orders.services.ownership.signing.loads',
            side_effect=signing.SignatureExpired('expired'),
        ):
            self.assertFalse(verify_order_access_token(self.order, token))
            resp = self.client.get(url, {'t': token})
        self.assertEqual(resp.status_code, 404)

    def test_retry_payment_ignores_token(self):
        token = make_order_access_token(self.order)
        url = reverse(
            'orders:retry_payment',
            kwargs={'order_number': self.order.order_number},
        )
        resp = self.client.get(url, {'t': token})
        self.assertEqual(resp.status_code, 404)

    def test_payment_error_owner_check(self):
        url = reverse(
            'orders:payment_error',
            kwargs={'order_number': self.order.order_number},
        )
        self.assertEqual(self.client.get(url).status_code, 404)
        token = make_order_access_token(self.order)
        self.assertEqual(self.client.get(url, {'t': token}).status_code, 200)
        self.client.login(email='token-owner@example.com', password='pass12345')
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_liqpay_result_url_contains_token(self):
        self._session_cart()
        self.client.get(reverse('orders:checkout'))
        resp = self.client.get(
            reverse('orders:checkout_step', kwargs={'step': 4}),
        )
        self.assertEqual(resp.status_code, 200)
        order = resp.context['order']
        liqpay = resp.context['liqpay']
        payload = json.loads(base64.b64decode(liqpay['data']).decode())
        self.assertIn('t=', payload['result_url'])
        self.assertIn(order.order_number, payload['result_url'])


@override_settings(STORAGES=TEST_STORAGES)
class TemplateNoOyra15OrdersSide(TestCase):
    def test_cart_detail_response_has_no_oyra15(self):
        category = Category.objects.create(name='T', is_active=True)
        product = Product.objects.create(
            category=category,
            name='P',
            sku='SKU-T',
            price=Decimal('100'),
            stock_quantity=1,
            is_active=True,
        )
        session = self.client.session
        session['oyra_cart'] = {str(product.pk): 1}
        session.save()
        resp = self.client.get(reverse('cart:detail'))
        self.assertNotContains(resp, 'OYRA15')
        self.assertContains(resp, 'placeholder="Промокод"')
