"""Сигнали замовлень: SMS клієнту + сповіщення адмінам при створенні."""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Order
from .services.admin_order_notify import notify_admins_new_order
from .services.order_notify import notify_order_status


@receiver(pre_save, sender=Order)
def order_store_previous_status(sender, instance: Order, **kwargs):
    if not instance.pk:
        instance._previous_status = None  # noqa: SLF001
        return
    try:
        previous = Order.objects.only('status').get(pk=instance.pk)
        instance._previous_status = previous.status  # noqa: SLF001
    except Order.DoesNotExist:
        instance._previous_status = None  # noqa: SLF001


@receiver(post_save, sender=Order)
def order_status_sms(sender, instance: Order, created: bool, **kwargs):
    previous = getattr(instance, '_previous_status', None)
    if created:
        notify_order_status(instance, status=instance.status)
        # Адмінам — після вибору способу оплати (коли вже є payment_method і контакти).
        # На create з кошика контакти ще порожні — див. notify після step 4.
        return
    if previous is None or previous == instance.status:
        return
    notify_order_status(instance, status=instance.status)


def notify_admins_after_checkout(order: Order) -> None:
    """Викликати з checkout після фіналізації кроку оплати."""
    notify_admins_new_order(order)
