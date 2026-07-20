"""Парсер YML/XML вигрузки Siker (Yandex Market format)."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Iterable
from urllib.request import Request, urlopen

DEFAULT_EXPORT_URL = (
    'https://dev.siker.ua/export/255/export_2106_6a5731261d4fb.yml'
)

_CDATA_RE = re.compile(
    r'<!\[CDATA\[(.*?)\]\]>',
    re.DOTALL | re.IGNORECASE,
)
_TAG_RE = re.compile(r'<[^>]+>')
_WS_RE = re.compile(r'\s+')


@dataclass
class YmlCategory:
    external_id: str
    name: str
    parent_id: str | None = None


@dataclass
class YmlOffer:
    external_id: str
    vendor_code: str
    name: str
    price: Decimal
    price_drop: Decimal | None
    currency_id: str
    available: bool
    category_id: str
    stock_quantity: int | None
    pictures: list[str] = field(default_factory=list)
    params: dict[str, str] = field(default_factory=dict)
    description_html: str = ''
    url: str = ''


@dataclass
class YmlCatalog:
    shop_name: str
    categories: list[YmlCategory]
    offers: list[YmlOffer]


def fetch_yml_bytes(url: str, timeout: int = 120) -> bytes:
    req = Request(url, headers={'User-Agent': 'OyraSikerImport/1.0'})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — URL з CLI/адміна
        return resp.read()


def load_yml_bytes(source: str | None = None, file_path: str | None = None) -> bytes:
    if file_path:
        with open(file_path, 'rb') as fh:
            return fh.read()
    return fetch_yml_bytes(source or DEFAULT_EXPORT_URL)


def unescape_text(value: str) -> str:
    """Подвійне unescape для `&amp;apos;` / `&amp;#39;` з вигрузки."""
    if not value:
        return ''
    text = html.unescape(value.strip())
    text = html.unescape(text)
    return text.replace('\xa0', ' ').strip()


def _text(el: ET.Element | None, default: str = '') -> str:
    if el is None or el.text is None:
        return default
    return unescape_text(el.text)


def _decimal(raw: str) -> Decimal:
    try:
        return Decimal(raw.strip().replace(',', '.'))
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f'Некоректна ціна: {raw!r}') from exc


def clean_description_html(raw: str) -> str:
    """Розкодовує entities / CDATA і повертає HTML-опис."""
    if not raw:
        return ''
    text = html.unescape(raw.strip())
    match = _CDATA_RE.search(text)
    if match:
        text = match.group(1)
    text = html.unescape(text)
    return text.strip()


def html_to_plain(html_text: str, max_len: int = 400) -> str:
    plain = _TAG_RE.sub(' ', html_text or '')
    plain = html.unescape(plain)
    plain = _WS_RE.sub(' ', plain).strip()
    if len(plain) <= max_len:
        return plain
    return plain[: max_len - 1].rstrip() + '…'


def parse_yml(data: bytes | str) -> YmlCatalog:
    if isinstance(data, bytes):
        # Файл може починатися з markdown-обгортки Cursor upload — шукаємо XML
        text = data.decode('utf-8', errors='replace')
    else:
        text = data

    xml_start = text.find('<?xml')
    if xml_start == -1:
        xml_start = text.find('<yml_catalog')
    if xml_start > 0:
        text = text[xml_start:]

    root = ET.fromstring(text)
    shop = root.find('shop')
    if shop is None:
        raise ValueError('У YML немає вузла <shop>')

    categories: list[YmlCategory] = []
    cats_el = shop.find('categories')
    if cats_el is not None:
        for cat in cats_el.findall('category'):
            cid = cat.get('id')
            if not cid:
                continue
            categories.append(
                YmlCategory(
                    external_id=cid,
                    name=_text(cat),
                    parent_id=cat.get('parentId'),
                )
            )

    offers: list[YmlOffer] = []
    offers_el = shop.find('offers')
    if offers_el is not None:
        for offer in offers_el.findall('offer'):
            oid = offer.get('id') or ''
            vendor = _text(offer.find('vendorCode'))
            name = _text(offer.find('name'))
            price_raw = _text(offer.find('price'))
            if not vendor or not name or not price_raw:
                continue

            price_drop_raw = _text(offer.find('priceDrop'))
            price = _decimal(price_raw)
            price_drop = _decimal(price_drop_raw) if price_drop_raw else None

            stock_raw = _text(offer.find('stock_quantity'))
            stock = int(stock_raw) if stock_raw.isdigit() else None

            params: dict[str, str] = {}
            for param in offer.findall('param'):
                pname = (param.get('name') or '').strip()
                if pname:
                    params[pname] = _text(param)

            pictures = [
                _text(pic)
                for pic in offer.findall('picture')
                if _text(pic)
            ]

            available_raw = _text(offer.find('available'), 'true').lower()
            offers.append(
                YmlOffer(
                    external_id=oid,
                    vendor_code=vendor,
                    name=name,
                    price=price,
                    price_drop=price_drop,
                    currency_id=_text(offer.find('currencyId'), 'UAH'),
                    available=available_raw in ('true', '1', 'yes'),
                    category_id=_text(offer.find('categoryId')),
                    stock_quantity=stock,
                    pictures=pictures,
                    params=params,
                    description_html=clean_description_html(
                        _text(offer.find('description'))
                    ),
                    url=_text(offer.find('url')),
                )
            )

    return YmlCatalog(
        shop_name=_text(shop.find('name'), 'Siker'),
        categories=categories,
        offers=offers,
    )


def download_image(url: str, timeout: int = 60) -> tuple[bytes, str]:
    """Повертає (bytes, filename)."""
    req = Request(url, headers={'User-Agent': 'OyraSikerImport/1.0'})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310
        data = resp.read()
        path = url.rsplit('/', 1)[-1].split('?', 1)[0] or 'image.jpg'
        return data, path


def iter_category_roots(categories: Iterable[YmlCategory]) -> list[YmlCategory]:
    return [c for c in categories if not c.parent_id]
