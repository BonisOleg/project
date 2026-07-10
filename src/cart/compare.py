from django.conf import settings


class CompareService:
    def __init__(self, request):
        self.request = request
        self.session_key = settings.COMPARE_SESSION_KEY
        self.max_items = settings.COMPARE_MAX_ITEMS
        if self.session_key not in request.session:
            request.session[self.session_key] = []

    @property
    def ids(self):
        return self.request.session.get(self.session_key, [])

    def add(self, product_id):
        ids = list(self.ids)
        pid = int(product_id)
        if pid in ids:
            return False
        if len(ids) >= self.max_items:
            return False
        ids.append(pid)
        self.request.session[self.session_key] = ids
        self.request.session.modified = True
        return True

    def remove(self, product_id):
        ids = [i for i in self.ids if i != int(product_id)]
        self.request.session[self.session_key] = ids
        self.request.session.modified = True

    def clear(self):
        self.request.session[self.session_key] = []
        self.request.session.modified = True

    def get_products(self):
        from src.catalog.models import Product
        if not self.ids:
            return []
        products = {
            p.pk: p
            for p in Product.objects.active()
            .filter(pk__in=self.ids)
            .annotate_rating()
            .prefetch_related('images', 'attributes')
        }
        return [products[pid] for pid in self.ids if pid in products]

    @property
    def count(self):
        return len(self.ids)
