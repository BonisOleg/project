import base64
import hashlib
import json
import logging

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
        return self._sign(data_b64) == signature

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
