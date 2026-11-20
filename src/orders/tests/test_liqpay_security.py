from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from src.orders.models import Order
from src.orders.services.liqpay import LiqPayService


def _signed_callback(payload):
    service = LiqPayService()
    data = service._encode(payload)
    return data, service._sign(data)


@override_settings(
    LIQPAY_PUBLIC_KEY='test_public',
    LIQPAY_PRIVATE_KEY='test_private',
    LIQPAY_SANDBOX=False,
)
class LiqPayCallbackSecurityTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            first_name='Іван',
            last_name='Тест',
            phone='+380501112233',
            email='buyer@example.com',
            delivery_service=Order.DELIVERY_NP,
            delivery_city='Київ',
            delivery_address='Відділення 1',
            subtotal=Decimal('850.00'),
            total=Decimal('850.00'),
            liqpay_order_id='liqpay-sec-001',
        )

    def _post(self, **extra):
        payload = {
            'order_id': self.order.liqpay_order_id,
            'status': 'success',
            'transaction_id': 'tx-sec',
            'amount': format(self.order.total, 'f'),
            'currency': 'UAH',
        }
        payload.update(extra)
        data, signature = _signed_callback(payload)
        return self.client.post(
            reverse('orders:liqpay_callback'),
            {'data': data, 'signature': signature},
        )

    def test_matching_success_marks_paid_once(self):
        first = self._post()
        second = self._post()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PAID)

    def test_sandbox_is_rejected_when_sandbox_disabled(self):
        response = self._post(status='sandbox')
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PENDING)

    def test_amount_mismatch_is_rejected(self):
        response = self._post(amount='1.00')
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PENDING)

    def test_bad_signature_is_forbidden(self):
        response = self.client.post(reverse('orders:liqpay_callback'), {
            'data': 'bm90LWpzb24=',
            'signature': 'wrong',
        })
        self.assertEqual(response.status_code, 403)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PENDING)
