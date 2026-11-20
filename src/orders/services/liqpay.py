import base64
import hashlib
import hmac
import json
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings

logger = logging.getLogger(__name__)

LIQPAY_CHECKOUT_URL = 'https://www.liqpay.ua/api/3/checkout'


class LiqPayService:
    def __init__(self):
        self.public_key = settings.LIQPAY_PUBLIC_KEY
        self.private_key = settings.LIQPAY_PRIVATE_KEY

    def _encode(self, payload):
        return base64.b64encode(
            json.dumps(payload, ensure_ascii=False).encode(),
        ).decode()

    def _sign(self, data_b64):
        raw = (self.private_key + data_b64 + self.private_key).encode()
        return base64.b64encode(hashlib.sha1(raw).digest()).decode()

    def decode_data(self, data_b64):
        try:
            return json.loads(base64.b64decode(data_b64).decode())
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error('LiqPay decode: %s', exc)
            return {}

    def verify_callback(self, data_b64, signature):
        if not self.private_key or not data_b64 or not signature:
            return False
        expected = self._sign(data_b64)
        try:
            return hmac.compare_digest(expected, signature)
        except (TypeError, ValueError):
            return False

    def payment_is_acceptable(self, order, payload) -> bool:
        status = (payload or {}).get('status')
        if status == 'sandbox':
            if not settings.LIQPAY_SANDBOX:
                return False
        elif status != 'success':
            return False
        if str((payload or {}).get('currency') or '').upper() != 'UAH':
            return False
        try:
            amount = Decimal(str(payload.get('amount')))
        except (InvalidOperation, TypeError, ValueError, ArithmeticError):
            return False
        return abs(amount - Decimal(order.total)) <= Decimal('0.01')

    def create_checkout(self, order, result_url, server_url):
        payload = {
            'public_key': self.public_key,
            'version': 3,
            'action': 'pay',
            'amount': float(order.total),
            'currency': 'UAH',
            'description': f'Замовлення {order.order_number}',
            'order_id': order.liqpay_order_id or order.order_number,
            'result_url': result_url,
            'server_url': server_url,
        }
        if settings.LIQPAY_SANDBOX:
            payload['sandbox'] = 1
        data = self._encode(payload)
        return {
            'data': data,
            'signature': self._sign(data),
            'checkout_url': LIQPAY_CHECKOUT_URL,
        }
