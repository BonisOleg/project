from django.utils import translation


class AdminUkrainianMiddleware:
    """Завжди українська мова в /admin/ (ігнорує Accept-Language браузера)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            translation.activate('uk')
            request.LANGUAGE_CODE = 'uk'

        response = self.get_response(request)

        if request.path.startswith('/admin/'):
            response.headers.setdefault('Content-Language', 'uk')

        return response
