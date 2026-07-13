import json
import logging
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

NP_API_URL = 'https://api.novaposhta.ua/v2.0/json/'
REQUEST_TIMEOUT = 8


class NovaPoshtaError(Exception):
    pass


class NovaPoshtaService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else getattr(settings, 'NOVA_POSHTA_API_KEY', '')

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _call(self, model: str, method: str, props: dict[str, Any] | None = None) -> list[dict]:
        if not self.api_key:
            raise NovaPoshtaError('NOVA_POSHTA_API_KEY is not configured')
        payload = {
            'apiKey': self.api_key,
            'modelName': model,
            'calledMethod': method,
            'methodProperties': props or {},
        }
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(
            NP_API_URL,
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read().decode('utf-8'))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            logger.warning('Nova Poshta request failed: %s', exc)
            raise NovaPoshtaError('Помилка запиту до Нової Пошти') from exc

        if not data.get('success'):
            errors = data.get('errors') or data.get('warnings') or ['Unknown error']
            logger.info('Nova Poshta API error: %s', errors)
            raise NovaPoshtaError('; '.join(str(e) for e in errors))

        return data.get('data') or []

    def search_cities(self, query: str, limit: int = 20) -> list[dict]:
        query = (query or '').strip()
        if len(query) < 2:
            return []
        rows = self._call('Address', 'searchSettlements', {
            'CityName': query,
            'Limit': str(limit),
        })
        results = []
        for block in rows:
            for item in block.get('Addresses') or []:
                ref = item.get('DeliveryCity') or item.get('Ref') or ''
                present = item.get('Present') or item.get('MainDescription') or ''
                if not ref or not present:
                    continue
                results.append({
                    'ref': ref,
                    'name': present,
                    'area': item.get('Area') or '',
                })
        return results[:limit]

    def search_warehouses(
        self,
        city_ref: str,
        query: str = '',
        delivery_type: str = 'warehouse',
        limit: int = 50,
    ) -> list[dict]:
        city_ref = (city_ref or '').strip()
        if not city_ref:
            return []
        props: dict[str, Any] = {
            'CityRef': city_ref,
            'Limit': str(limit),
        }
        query = (query or '').strip()
        if query:
            props['FindByString'] = query

        rows = self._call('Address', 'getWarehouses', props)
        results = []
        for item in rows:
            category = item.get('CategoryOfWarehouse') or ''
            if delivery_type == 'postomat' and category != 'Postomat':
                continue
            if delivery_type == 'warehouse' and category == 'Postomat':
                continue
            description = item.get('Description') or item.get('DescriptionRu') or ''
            ref = item.get('Ref') or ''
            if not description or not ref:
                continue
            results.append({
                'ref': ref,
                'name': description,
                'number': item.get('Number') or '',
            })
        return results[:limit]
