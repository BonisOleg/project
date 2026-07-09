import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DONE = 'done'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Очікує оплати'),
        (STATUS_PAID, 'Оплачено'),
        (STATUS_PROCESSING, 'В обробці'),
        (STATUS_SHIPPED, 'Відправлено'),
        (STATUS_DONE, 'Виконано'),
        (STATUS_CANCELLED, 'Скасовано'),
    ]

    DELIVERY_NP = 'nova_poshta'
    DELIVERY_UP = 'ukrposhta'
    DELIVERY_CHOICES = [
        (DELIVERY_NP, 'Нова Пошта'),
        (DELIVERY_UP, 'Укрпошта'),
    ]

    NP_WAREHOUSE = 'warehouse'
    NP_POSTOMAT = 'postomat'
    NP_COURIER = 'courier'
    NP_TYPE_CHOICES = [
        (NP_WAREHOUSE, 'Відділення'),
        (NP_POSTOMAT, 'Поштомат'),
        (NP_COURIER, "Кур'єр"),
    ]

    order_number = models.CharField('Номер', max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='orders',
    )
    first_name = models.CharField('Імʼя', max_length=100)
    last_name = models.CharField('Прізвище', max_length=100)
    phone = models.CharField('Телефон', max_length=30)
    email = models.EmailField('Email')
    comment = models.TextField('Коментар', blank=True)
    delivery_service = models.CharField('Доставка', max_length=20, choices=DELIVERY_CHOICES)
    delivery_city = models.CharField('Місто', max_length=150)
    delivery_type = models.CharField(
        'Тип НП', max_length=20, choices=NP_TYPE_CHOICES, blank=True,
    )
    delivery_address = models.CharField('Адреса / відділення', max_length=255)
    subtotal = models.DecimalField('Сума товарів', max_digits=10, decimal_places=2)
    discount = models.DecimalField('Знижка', max_digits=10, decimal_places=2, default=0)
    delivery_cost = models.DecimalField('Доставка', max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField('Разом', max_digits=10, decimal_places=2)
    promo_code = models.CharField('Промокод', max_length=50, blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    liqpay_order_id = models.CharField('LiqPay order ID', max_length=64, blank=True)
    liqpay_transaction_id = models.CharField('LiqPay transaction', max_length=64, blank=True)
    tracking_number = models.CharField('ТТН', max_length=64, blank=True)
    idempotency_key = models.CharField(max_length=64, unique=True, editable=False)
    create_account = models.BooleanField('Створити акаунт', default=False)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f'OY{uuid.uuid4().hex[:8].upper()}'
        if not self.idempotency_key:
            self.idempotency_key = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('orders:thank_you', kwargs={'order_number': self.order_number})


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT)
    product_name = models.CharField(max_length=300)
    product_sku = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Позиція замовлення'
        verbose_name_plural = 'Позиції замовлення'
