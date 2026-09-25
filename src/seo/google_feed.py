"""Google Merchant Center product feed (RSS 2.0 + g: namespace)."""

from __future__ import annotations

import re
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring

from django.utils.html import strip_tags

from src.catalog.models import Product
from src.core.models import SiteSettings

G_NS = 'http://base.google.com/ns/1.0'
register_namespace('g', G_NS)

AVAILABILITY_MAP = {
    Product.AVAIL_IN_STOCK: 'in_stock',
    Product.AVAIL_OUT: 'out_of_stock',
    Product.AVAIL_EXPECTED: 'preorder',
}
_WS_RE = re.compile(r'\s+')


def _text(value: str) -> str:
    return _WS_RE.sub(' ', strip_tags(value or '')).strip()


def _money(amount: Decimal) -> str:
    return f'{amount.quantize(Decimal("0.01"))} UAH'


def _g(parent: Element, tag: str, text: str | None = None) -> Element:
    el = SubElement(parent, f'{{{G_NS}}}{tag}')
    if text is not None:
        el.text = text
    return el


def _absolute_media_url(request, image_field) -> str | None:
    if not image_field or not getattr(image_field, 'name', None):
        return None
    return request.build_absolute_uri(image_field.url)


def build_google_feed_xml(request) -> bytes:
    settings_obj = SiteSettings.get_solo()
    site_name = settings_obj.site_name or 'Oyra'
    home_url = request.build_absolute_uri('/')

    rss = Element('rss', {'version': '2.0'})
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = site_name
    SubElement(channel, 'link').text = home_url
    SubElement(channel, 'description').text = f'Каталог {site_name} для Google Ads'

    products = (
        Product.objects.on_storefront()
        .select_related('category', 'brand')
        .prefetch_related('images')
        .order_by('id')
    )

    for product in products:
        images = list(product.images.all())
        if not images:
            continue

        main = next((img for img in images if img.is_main), images[0])
        image_url = _absolute_media_url(request, main.image)
        if not image_url:
            continue

        item = SubElement(channel, 'item')
        _g(item, 'id', product.sku)
        SubElement(item, 'title').text = _text(product.name)[:150]
        description = (
            _text(product.description)
            or _text(product.short_description)
            or _text(product.name)
        )
        SubElement(item, 'description').text = description[:5000]
        SubElement(item, 'link').text = request.build_absolute_uri(product.get_absolute_url())
        _g(item, 'image_link', image_url)

        extra_count = 0
        for img in images:
            if img.pk == main.pk:
                continue
            extra_url = _absolute_media_url(request, img.image)
            if not extra_url:
                continue
            _g(item, 'additional_image_link', extra_url)
            extra_count += 1
            if extra_count >= 10:
                break

        _g(item, 'availability', AVAILABILITY_MAP.get(product.availability, 'out_of_stock'))
        _g(item, 'condition', 'new')
        if product.brand_id and product.brand:
            _g(item, 'brand', _text(product.brand.name)[:70])
        if product.category_id and product.category:
            _g(item, 'product_type', _text(product.category.name))

        if product.old_price and product.old_price > product.price:
            _g(item, 'price', _money(product.old_price))
            _g(item, 'sale_price', _money(product.price))
        else:
            _g(item, 'price', _money(product.price))

        _g(item, 'identifier_exists', 'no')

    xml_body = tostring(rss, encoding='utf-8', method='xml')
    return b"<?xml version='1.0' encoding='utf-8'?>" + xml_body
