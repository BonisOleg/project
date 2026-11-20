"""Редирект лише на цей хост. Зовнішній Referer ігнорується."""

from django.utils.http import url_has_allowed_host_and_scheme


def safe_next(request, default='/'):
    target = request.META.get('HTTP_REFERER') or ''
    if target and url_has_allowed_host_and_scheme(
        url=target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return default
