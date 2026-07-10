from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from src.core.breadcrumbs import make_breadcrumbs

from .compare import CompareService
from .services import CartService


def cart_detail(request):
    cart = CartService(request)
    promo_code = request.session.get('promo_code', '')
    promo = cart.apply_promo(promo_code) if promo_code else None
    return render(request, 'cart/detail.html', {
        'lines': cart.get_lines(),
        'subtotal': cart.subtotal,
        'promo': promo,
        'total': cart.total(promo),
        'page_title': 'Кошик',
        'breadcrumbs': make_breadcrumbs(('Кошик', '')),
    })


@require_POST
def cart_add(request, product_id):
    cart = CartService(request)
    qty = int(request.POST.get('quantity', 1))
    cart.add(product_id, qty)
    if request.htmx:
        html = render_to_string('partials/cart_count.html', {
            'cart_count': cart.count,
            'toast_message': 'Товар додано',
            'toast_tag': 'success',
        })
        return HttpResponse(html)
    messages.success(request, 'Товар додано до кошика')
    return redirect('cart:detail')


def _cart_htmx_context(request, cart):
    promo_code = request.session.get('promo_code', '')
    promo = cart.apply_promo(promo_code) if promo_code else None
    return {
        'lines': cart.get_lines(),
        'subtotal': cart.subtotal,
        'promo': promo,
        'total': cart.total(promo),
    }


@require_POST
def cart_update(request, product_id):
    cart = CartService(request)
    qty = int(request.POST.get('quantity', 1))
    cart.set_quantity(product_id, qty)
    if request.htmx:
        return render(request, 'cart/_cart_lines.html', _cart_htmx_context(request, cart))
    return redirect('cart:detail')


@require_POST
def cart_remove(request, product_id):
    cart = CartService(request)
    cart.remove(product_id)
    if request.htmx:
        return render(request, 'cart/_cart_lines.html', _cart_htmx_context(request, cart))
    return redirect('cart:detail')


@require_POST
def apply_promo(request):
    cart = CartService(request)
    code = request.POST.get('promo_code', '').strip()
    promo = cart.apply_promo(code)
    if promo:
        request.session['promo_code'] = code
        messages.success(request, 'Промокод застосовано')
    else:
        request.session.pop('promo_code', None)
        messages.error(request, 'Невірний або прострочений промокод')
    return redirect('cart:detail')


def mini_cart(request):
    cart = CartService(request)
    return render(request, 'partials/mini_cart.html', {
        'lines': cart.get_lines()[:5],
        'subtotal': cart.subtotal,
        'cart_count': cart.count,
    })


@require_POST
def compare_add(request, product_id):
    svc = CompareService(request)
    pid = int(product_id)
    if pid in svc.ids:
        messages.info(request, 'Товар уже в порівнянні')
    elif svc.add(product_id):
        messages.success(request, 'Додано до порівняння')
    else:
        messages.warning(request, f'Максимум {svc.max_items} товарів для порівняння')
    if request.htmx:
        return render(request, 'partials/compare_count.html', {'compare_count': svc.count})
    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def compare_remove(request, product_id):
    svc = CompareService(request)
    svc.remove(product_id)
    if request.htmx:
        return render(request, 'partials/compare_count.html', {'compare_count': svc.count})
    return redirect('catalog:compare')
