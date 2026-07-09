from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/<int:step>/', views.checkout, name='checkout_step'),
    path('checkout/', views.checkout, {'step': 1}, name='checkout'),
    path('thank-you/<str:order_number>/', views.thank_you, name='thank_you'),
    path('payment-error/<str:order_number>/', views.payment_error, name='payment_error'),
    path('retry/<str:order_number>/', views.retry_payment, name='retry_payment'),
    path('liqpay/callback/', views.liqpay_callback, name='liqpay_callback'),
]
