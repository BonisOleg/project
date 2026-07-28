from django.conf import settings
from django.utils import translation


class AdminUkrainianMiddleware:
    """Завжди українська мова в адмінці (ігнорує Accept-Language браузера)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self._admin_prefix = f'/{settings.ADMIN_URL.lstrip("/")}'

    def _is_admin(self, request) -> bool:
        return request.path.startswith(self._admin_prefix)

    def __call__(self, request):
        if self._is_admin(request):
            translation.activate('uk')
            request.LANGUAGE_CODE = 'uk'

        response = self.get_response(request)

        if self._is_admin(request):
            response.headers.setdefault('Content-Language', 'uk')

        return response
