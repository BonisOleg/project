from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


def _clear_session_promo(sender, request, **kwargs):
    if request is None:
        return
    session = getattr(request, 'session', None)
    if session is None:
        return
    session.pop('promo_code', None)


@receiver(user_logged_in)
def clear_promo_on_login(sender, request, user, **kwargs):
    _clear_session_promo(sender, request, **kwargs)


@receiver(user_logged_out)
def clear_promo_on_logout(sender, request, user, **kwargs):
    _clear_session_promo(sender, request, **kwargs)
