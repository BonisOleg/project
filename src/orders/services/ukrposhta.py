import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

UP_CLASSIFIER_URL = 'https://www.ukrposhta.ua/address-classifier-ws/'
REQUEST_TIMEOUT = 10


class UkrposhtaError(Exception):
    pass


class UkrposhtaService:
    """Ukrposhta Address Classifier API (cities + post offices)."""

    def __init__(self, bearer: str | None = None):
        self.bearer = bearer if bearer is not None else getattr(settings, 'UKRPOSHTA_BEARER', '')

    @property
    def configured(self) -> bool:
        return bool(self.bearer)

    def _entries(self, data: Any) -> list[dict]:
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if not isinstance(data, dict):
            return []
        entries = data.get('Entries') or data.get('entries') or {}
        if isinstance(entries, list):
            return [row for row in entries if isinstance(row, dict)]
        if isinstance(entries, dict):
            entry = entries.get('Entry') or entries.get('entry') or []
            if isinstance(entry, dict):
                return [entry]
            if isinstance(entry, list):
                return [row for row in entry if isinstance(row, dict)]
        entry = data.get('Entry') or data.get('entry')
        if isinstance(entry, dict):
            return [entry]
        if isinstance(entry, list):
            return [row for row in entry if isinstance(row, dict)]
        return []

    def _get(self, endpoint: str, params: dict[str, Any]) -> list[dict]:
        if not self.bearer:
            raise UkrposhtaError('UKRPOSHTA_BEARER is not configured')
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, '')})
        url = f'{UP_CLASSIFIER_URL}{endpoint.lstrip("/")}?{query}'
        request = urllib.request.Request(
            url,
            headers={
                'Authorization': f'Bearer {self.bearer}',
                'Accept': 'application/json',
            },
            method='GET',
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                raw = response.read().decode('utf-8')
                data = json.loads(raw) if raw.strip() else {}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            logger.warning('Ukrposhta request failed: %s', exc)
            raise UkrposhtaError('Помилка запиту до Укрпошти') from exc
        return self._entries(data)

    def search_cities(self, query: str, limit: int = 20) -> list[dict]:
        query = (query or '').strip()
        if len(query) < 2:
            return []
        rows = self._get('get_city_by_region_id_and_district_id_and_city_ua', {
            'city_ua': query,
        })
        results = []
        seen = set()
        for item in rows:
            city_id = str(item.get('CITY_ID') or item.get('city_id') or '').strip()
            city_name = (
                item.get('CITY_UA')
                or item.get('CITY_NAME')
                or item.get('city_ua')
                or ''
            ).strip()
            if not city_id or not city_name or city_id in seen:
                continue
            seen.add(city_id)
            region = (item.get('REGION_UA') or item.get('REGION_NAME') or '').strip()
            district = (item.get('DISTRICT_UA') or item.get('DISTRICT_NAME') or '').strip()
            city_type = (item.get('SHORTCITYTYPE_UA') or item.get('CITYTYPE_UA') or '').strip()
            display = f'{city_type} {city_name}'.strip() if city_type else city_name
            area_parts = [p for p in (district, region) if p]
            results.append({
                'ref': city_id,
                'name': display,
                'area': ', '.join(area_parts),
                'region_id': str(item.get('REGION_ID') or ''),
                'district_id': str(item.get('DISTRICT_ID') or ''),
            })
            if len(results) >= limit:
                break
        return results

    def search_postoffices(
        self,
        city_id: str,
        query: str = '',
        region_id: str = '',
        district_id: str = '',
        limit: int = 50,
    ) -> list[dict]:
        city_id = (city_id or '').strip()
        if not city_id:
            return []
        params: dict[str, Any] = {'city_id': city_id}
        if region_id:
            params['region_id'] = region_id
        if district_id:
            params['district_id'] = district_id
        query = (query or '').strip()
        if query.isdigit() and len(query) >= 3:
            params['postindex'] = query

        rows = self._get('get_postoffices_by_city_id', params)
        results = []
        q_lower = query.lower()
        for item in rows:
            lock_code = str(item.get('LOCK_CODE') or '0')
            if lock_code not in ('0', ''):
                continue
            if str(item.get('IS_SECURITY') or '0') == '1':
                continue
            postindex = str(item.get('POSTINDEX') or item.get('TECHINDEX') or '').strip()
            short_name = (item.get('PO_SHORT') or '').strip()
            long_name = (item.get('PO_LONG') or '').strip()
            address = (item.get('ADDRESS') or '').strip()
            label = short_name or long_name or postindex
            if address and address not in label:
                label = f'{label}, {address}' if label else address
            if postindex and postindex not in label:
                label = f'{postindex} — {label}' if label else postindex
            if not label:
                continue
            if q_lower and not query.isdigit() and q_lower not in label.lower():
                continue
            results.append({
                'ref': str(item.get('ID') or postindex),
                'name': label,
                'number': postindex,
            })
            if len(results) >= limit:
                break
        return results
