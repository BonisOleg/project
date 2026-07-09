import uuid

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from src.cart.services import CartService

from .forms import CheckoutStep2Form, CheckoutStep3Form
from .models import Order, OrderItem
from .services.liqpay import LiqPayService

User = get_user_model()


def _get_checkout_order(request):
    order_id = request.session.get('checkout_order_id')
    if order_id:
        try:
            return Order.objects.get(pk=order_id, status=Order.STATUS_PENDING)
        except Order.DoesNotExist:
            pass
    return None


def _create_order_from_cart(request):
    cart = CartService(request)
    lines = cart.get_lines()
    if not lines:
        return None
    promo_code = request.session.get('promo_code', '')
    promo = cart.apply_promo(promo_code) if promo_code else None
    subtotal = cart.subtotal
    discount = subtotal - cart.total(promo) if promo else 0
    total = cart.total(promo)
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        first_name=request.user.first_name if request.user.is_authenticated else '',
        last_name=request.user.last_name if request.user.is_authenticated else '',
        phone=getattr(request.user, 'phone', '') if request.user.is_authenticated else '',
        email=request.user.email if request.user.is_authenticated else '',
        subtotal=subtotal,
        discount=discount,
        total=total,
        promo_code=promo_code,
        delivery_service=Order.DELIVERY_NP,
        delivery_city='',
        delivery_address='',
        liqpay_order_id=uuid.uuid4().hex[:16],
    )
    for line in lines:
        OrderItem.objects.create(
            order=order,
            product=line['product'],
            product_name=line['product'].name,
            product_sku=line['product'].sku,
            price=line['product'].price,
            quantity=line['quantity'],
            line_total=line['line_total'],
        )
    request.session['checkout_order_id'] = order.pk
    return order


def checkout(request, step=1):
    cart = CartService(request)
    if not cart.get_lines():
        messages.warning(request, 'Кошик порожній')
        return redirect('cart:detail')

    order = _get_checkout_order(request) or _create_order_from_cart(request)
    step = int(step)
    if step < 1 or step > 4:
        step = 1

    if step == 1:
        return render(request, 'orders/checkout_step1.html', {
            'order': order, 'lines': cart.get_lines(), 'step': step,
            'page_title': 'Оформлення — крок 1',
        })

    if step == 2:
        form = CheckoutStep2Form(request.POST or None, instance=order)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('orders:checkout_step', step=3)
        return render(request, 'orders/checkout_step2.html', {
            'form': form, 'order': order, 'step': step,
            'page_title': 'Оформлення — контактні дані',
        })

    if step == 3:
        form = CheckoutStep3Form(request.POST or None, instance=order)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('orders:checkout_step', step=4)
        return render(request, 'orders/checkout_step3.html', {
            'form': form, 'order': order, 'step': step,
            'page_title': 'Оформлення — доставка',
        })

    liqpay = LiqPayService()
    result_url = request.build_absolute_uri(
        reverse('orders:thank_you', kwargs={'order_number': order.order_number}),
    )
    server_url = request.build_absolute_uri(reverse('orders:liqpay_callback'))
    checkout_data = liqpay.create_checkout(order, result_url, server_url)
    return render(request, 'orders/checkout_step4.html', {
        'order': order, 'step': step, 'liqpay': checkout_data,
        'page_title': 'Оформлення — оплата',
    })


def thank_you(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if order.status == Order.STATUS_PAID:
        cart = CartService(request)
        cart.clear()
        request.session.pop('checkout_order_id', None)
        request.session.pop('promo_code', None)
    return render(request, 'orders/thank_you.html', {'order': order})


def payment_error(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/payment_error.html', {'order': order})


def retry_payment(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, status=Order.STATUS_PENDING)
    request.session['checkout_order_id'] = order.pk
    return redirect('orders:checkout_step', step=4)


@csrf_exempt
@require_POST
def liqpay_callback(request):
    data = request.POST.get('data', '')
    signature = request.POST.get('signature', '')
    svc = LiqPayService()
    if not svc.verify_callback(data, signature):
        return HttpResponse(status=403)

    payload = svc.decode_data(data)
    order_id = payload.get('order_id')
    status = payload.get('status')

    try:
        order = Order.objects.get(liqpay_order_id=order_id)
    except Order.DoesNotExist:
        try:
            order = Order.objects.get(order_number=order_id)
        except Order.DoesNotExist:
            return HttpResponse(status=404)

    if status in ('success', 'sandbox'):
        if order.status != Order.STATUS_PAID:
            order.status = Order.STATUS_PAID
            order.liqpay_transaction_id = payload.get('transaction_id', '')
            order.save(update_fields=['status', 'liqpay_transaction_id', 'updated_at'])
            if order.create_account and not order.user_id:
                _maybe_create_user(order)
    elif status in ('failure', 'error', 'reversed'):
        pass

    return HttpResponse('OK')


def _maybe_create_user(order):
    if User.objects.filter(email=order.email).exists():
        return
    user = User.objects.create_user(
        email=order.email,
        password=User.objects.make_random_password(),
        first_name=order.first_name,
        last_name=order.last_name,
        phone=order.phone,
    )
    order.user = user
    order.save(update_fields=['user'])
