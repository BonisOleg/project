from unittest.mock import MagicMock, patch

from django.db.models.signals import post_save
from django.test import SimpleTestCase, TestCase, override_settings

from src.orders.models import Order
from src.orders.signals import order_status_sms
from src.orders.services.order_notify import build_order_status_text, notify_order_status
from src.orders.services.turbosms import TurboSMSError, TurboSMSService, normalize_ua_phone


class NormalizePhoneTests(SimpleTestCase):
    def test_international(self):
        self.assertEqual(normalize_ua_phone('+380501112233'), '380501112233')

    def test_local_zero(self):
        self.assertEqual(normalize_ua_phone('050 111-22-33'), '380501112233')

    def test_nine_digits(self):
        self.assertEqual(normalize_ua_phone('501112233'), '380501112233')

    def test_invalid(self):
        self.assertIsNone(normalize_ua_phone('12345'))
        self.assertIsNone(normalize_ua_phone(''))


class TurboSMSServiceTests(SimpleTestCase):
    def test_can_send_requires_enabled_and_token_and_sender(self):
        svc = TurboSMSService(
            token='',
            sms_sender='Oyra',
            viber_sender='',
            enabled=True,
        )
        self.assertFalse(svc.can_send)

        svc = TurboSMSService(
            token='tok',
            sms_sender='Oyra',
            viber_sender='',
            enabled=False,
        )
        self.assertFalse(svc.can_send)

        svc = TurboSMSService(
            token='tok',
            sms_sender='Oyra',
            viber_sender='',
            enabled=True,
        )
        self.assertTrue(svc.can_send)

    @patch('src.orders.services.turbosms.urllib.request.urlopen')
    def test_hybrid_payload_when_both_senders(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = (
            b'{"response_code":802,"response_status":"SUCCESS_MESSAGE_PARTIAL_ACCEPTED",'
            b'"response_result":[]}'
        )
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        mock_urlopen.return_value = response

        svc = TurboSMSService(
            token='tok',
            sms_sender='OyraSMS',
            viber_sender='OyraViber',
            enabled=True,
            viber_ttl=3600,
        )
        result = svc.send('0501112233', 'Тест')
        self.assertTrue(result['ok'])

        request = mock_urlopen.call_args[0][0]
        body = request.data.decode('utf-8')
        self.assertIn('"sms"', body)
        self.assertIn('"viber"', body)
        self.assertIn('OyraSMS', body)
        self.assertIn('OyraViber', body)
        self.assertIn('380501112233', body)

    @patch('src.orders.services.turbosms.urllib.request.urlopen')
    def test_sms_only_when_no_viber_sender(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = (
            b'{"response_code":0,"response_status":"OK","response_result":[]}'
        )
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        mock_urlopen.return_value = response

        svc = TurboSMSService(
            token='tok',
            sms_sender='OyraSMS',
            viber_sender='',
            enabled=True,
        )
        svc.send('+380501112233', 'Тест')
        body = mock_urlopen.call_args[0][0].data.decode('utf-8')
        self.assertIn('"sms"', body)
        self.assertNotIn('"viber"', body)

    def test_invalid_phone_raises(self):
        svc = TurboSMSService(token='tok', sms_sender='Oyra', enabled=True)
        with self.assertRaises(TurboSMSError):
            svc.send('123', 'hi')


@override_settings(TURBOSMS_ENABLED=False)
class OrderNotifyTests(TestCase):
    def setUp(self):
        post_save.disconnect(order_status_sms, sender=Order)

    def tearDown(self):
        post_save.connect(order_status_sms, sender=Order)

    def _make_order(self, **kwargs):
        defaults = {
            'first_name': 'Іван',
            'last_name': 'Тест',
            'phone': '+380501112233',
            'email': 't@example.com',
            'delivery_service': Order.DELIVERY_NP,
            'delivery_city': 'Київ',
            'delivery_address': 'Відділення 1',
            'subtotal': '100.00',
            'total': '100.00',
            'status': Order.STATUS_PENDING,
        }
        defaults.update(kwargs)
        return Order.objects.create(**defaults)

    def test_build_text_for_all_statuses(self):
        order = self._make_order(tracking_number='20450123456789')
        for status in (
            Order.STATUS_PENDING,
            Order.STATUS_PAID,
            Order.STATUS_PROCESSING,
            Order.STATUS_SHIPPED,
            Order.STATUS_DONE,
            Order.STATUS_CANCELLED,
        ):
            text = build_order_status_text(order, status=status)
            self.assertIsNotNone(text)
            self.assertIn(order.order_number, text)
        shipped = build_order_status_text(order, status=Order.STATUS_SHIPPED)
        self.assertIn('20450123456789', shipped)

    @override_settings(
        TURBOSMS_ENABLED=True,
        TURBOSMS_TOKEN='tok',
        TURBOSMS_SMS_SENDER='Oyra',
        TURBOSMS_VIBER_SENDER='',
    )
    @patch('src.orders.services.order_notify.TurboSMSService.send')
    def test_notify_calls_send(self, mock_send):
        mock_send.return_value = {'ok': True}
        order = self._make_order()
        self.assertTrue(notify_order_status(order))
        mock_send.assert_called_once()

    @override_settings(TURBOSMS_ENABLED=False)
    @patch('src.orders.services.order_notify.TurboSMSService.send')
    def test_notify_skipped_when_disabled(self, mock_send):
        order = self._make_order()
        self.assertFalse(notify_order_status(order))
        mock_send.assert_not_called()


@override_settings(
    TURBOSMS_ENABLED=True,
    TURBOSMS_TOKEN='tok',
    TURBOSMS_SMS_SENDER='Oyra',
    TURBOSMS_VIBER_SENDER='',
)
class OrderSmsSignalTests(TestCase):
    @patch('src.orders.signals.notify_order_status')
    def test_signal_on_create_and_status_change(self, mock_notify):
        mock_notify.return_value = True
        order = Order.objects.create(
            first_name='Іван',
            last_name='Тест',
            phone='+380501112233',
            email='t@example.com',
            delivery_service=Order.DELIVERY_NP,
            delivery_city='Київ',
            delivery_address='Відділення 1',
            subtotal='100.00',
            total='100.00',
            status=Order.STATUS_PENDING,
        )
        self.assertEqual(mock_notify.call_count, 1)

        order.status = Order.STATUS_PAID
        order.save(update_fields=['status', 'updated_at'])
        self.assertEqual(mock_notify.call_count, 2)

        order.save(update_fields=['updated_at'])
        self.assertEqual(mock_notify.call_count, 2)
