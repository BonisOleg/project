from django.db.models import F

from src.orders.models import Order
from src.promotions.models import PromoCode


def mark_promo_used(order) -> bool:
    """
    Атомарно +1 до used_count промокоду рівно один раз на замовлення.
    Повертає True, якщо підрахунок виконано в цьому виклику.
    """
    if not (order.promo_code or '').strip():
        return False

    flipped = Order.objects.filter(pk=order.pk, promo_counted=False).update(
        promo_counted=True,
    )
    if flipped != 1:
        return False

    PromoCode.objects.filter(code__iexact=order.promo_code.strip()).update(
        used_count=F('used_count') + 1,
    )
    order.promo_counted = True
    return True
