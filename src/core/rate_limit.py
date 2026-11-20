"""Ліміт POST з одного IP. Спільний кеш (у production — таблиця БД)."""

from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

from src.core.client_ip import client_ip

RATE_LIMIT_MESSAGE = 'Забагато спроб. Спробуйте пізніше.'


def consume_rate_limit(request, scope: str, *, limit: int = 5, window: int = 600) -> bool:
    """True, якщо спроба ще в межах ліміту."""
    if not getattr(settings, 'RATE_LIMIT_ENABLED', True):
        return True
    key = f'rl:{scope}:{client_ip(request)}'
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)
        count = 1
    return count <= limit


def rate_limit(limit: int = 5, window: int = 600):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST' and not consume_rate_limit(
                request, request.path, limit=limit, window=window,
            ):
                return HttpResponse(
                    RATE_LIMIT_MESSAGE,
                    status=429,
                    content_type='text/plain; charset=utf-8',
                )
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
