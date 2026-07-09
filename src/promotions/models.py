from decimal import Decimal

from django.db import models
from django.utils import timezone


class PromoCode(models.Model):
    TYPE_PERCENT = 'percent'
    TYPE_FIXED = 'fixed'
    TYPE_CHOICES = [
        (TYPE_PERCENT, 'Відсоток'),
        (TYPE_FIXED, 'Фіксована сума'),
    ]

    code = models.CharField('Код', max_length=50, unique=True)
    discount_type = models.CharField('Тип', max_length=10, choices=TYPE_CHOICES)
    discount_value = models.DecimalField('Значення', max_digits=10, decimal_places=2)
    is_active = models.BooleanField('Активний', default=True)
    valid_from = models.DateTimeField('Дійсний з', null=True, blank=True)
    valid_until = models.DateTimeField('Дійсний до', null=True, blank=True)
    max_uses = models.PositiveIntegerField('Макс. використань', null=True, blank=True)
    used_count = models.PositiveIntegerField('Використано', default=0)

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоди'

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def apply_discount(self, subtotal):
        if self.discount_type == self.TYPE_PERCENT:
            discount = subtotal * (self.discount_value / Decimal('100'))
            return max(subtotal - discount, Decimal('0'))
        return max(subtotal - self.discount_value, Decimal('0'))
