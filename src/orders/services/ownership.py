from django.core import signing

OWN_ORDERS_SESSION_KEY = 'own_orders'
OWN_ORDERS_MAX = 20
ORDER_ACCESS_SALT = 'orders.thank_you'
ORDER_ACCESS_MAX_AGE = 7 * 24 * 60 * 60  # 7 днів


def remember_own_order(session, order) -> None:
    """Запам'ятовує замовлення в сесії гостя (останні OWN_ORDERS_MAX)."""
    raw = session.get(OWN_ORDERS_SESSION_KEY) or []
    ids = [x for x in raw if isinstance(x, int)]
    if order.pk not in ids:
        ids.append(order.pk)
    session[OWN_ORDERS_SESSION_KEY] = ids[-OWN_ORDERS_MAX:]
    session.modified = True


def make_order_access_token(order) -> str:
    """Підписаний токен доступу до thank_you / payment_error (SameSite=Strict)."""
    return signing.dumps(
        {'pk': order.pk, 'n': order.order_number},
        salt=ORDER_ACCESS_SALT,
    )


def verify_order_access_token(order, token, max_age=ORDER_ACCESS_MAX_AGE) -> bool:
    """Перевіряє токен для конкретного замовлення (підпис + max_age)."""
    if not token:
        return False
    try:
        data = signing.loads(token, salt=ORDER_ACCESS_SALT, max_age=max_age)
    except signing.BadSignature:
        return False
    return (
        isinstance(data, dict)
        and data.get('pk') == order.pk
        and data.get('n') == order.order_number
    )


def user_can_access_order(request, order, *, allow_token: bool = False) -> bool:
    """Власник: user FK, staff, session own_orders; опційно GET ?t= токен."""
    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        if getattr(user, 'is_staff', False):
            return True
        if order.user_id and order.user_id == user.id:
            return True
    own = request.session.get(OWN_ORDERS_SESSION_KEY) or []
    if order.pk in own:
        return True
    if allow_token:
        token = request.GET.get('t', '')
        if verify_order_access_token(order, token):
            return True
    return False
