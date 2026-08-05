"""Швидке оновлення ціни/наявності товару з changelist (AJAX)."""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from src.catalog.models import Product


@staff_member_required
@require_POST
def product_quick_update(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Невірний JSON'}, status=400)

    product_id = payload.get('id')
    if not product_id:
        return JsonResponse({'ok': False, 'error': 'Немає id'}, status=400)

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Товар не знайдено'}, status=404)

    update_fields: list[str] = []

    if 'price' in payload:
        try:
            price = Decimal(str(payload['price']).replace(',', '.'))
        except (InvalidOperation, TypeError, ValueError):
            return JsonResponse({'ok': False, 'error': 'Невірна ціна'}, status=400)
        if price < 0:
            return JsonResponse({'ok': False, 'error': 'Ціна не може бути відʼємною'}, status=400)
        product.price = price
        update_fields.append('price')

    if 'availability' in payload:
        availability = payload['availability']
        allowed = {c[0] for c in Product.AVAILABILITY_CHOICES}
        if availability not in allowed:
            return JsonResponse({'ok': False, 'error': 'Невірна наявність'}, status=400)
        product.availability = availability
        update_fields.append('availability')

    if not update_fields:
        return JsonResponse({'ok': False, 'error': 'Немає полів для оновлення'}, status=400)

    update_fields.append('updated_at')
    product.save(update_fields=update_fields)
    return JsonResponse({
        'ok': True,
        'id': product.pk,
        'price': str(product.price),
        'availability': product.availability,
    })
