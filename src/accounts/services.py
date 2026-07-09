from django.db import IntegrityError

from src.catalog.models import Product

from .models import WishlistItem

WISHLIST_SESSION_KEY = 'oyra_wishlist'


class WishlistService:
    def __init__(self, request):
        self.request = request
        self.user = request.user

    @property
    def is_authenticated(self):
        return self.user.is_authenticated

    def _session_ids(self):
        raw = self.request.session.get(WISHLIST_SESSION_KEY, [])
        if not isinstance(raw, list):
            return []
        return list(dict.fromkeys(int(x) for x in raw if str(x).isdigit()))

    def _save_session_ids(self, ids):
        self.request.session[WISHLIST_SESSION_KEY] = ids
        self.request.session.modified = True

    @property
    def count(self):
        return len(self.product_ids())

    def product_ids(self):
        if self.is_authenticated:
            return set(
                WishlistItem.objects.filter(user=self.user).values_list('product_id', flat=True)
            )
        return set(self._session_ids())

    def get_products(self):
        ids = self.product_ids()
        if not ids:
            return Product.objects.none()
        preserved = {pk: idx for idx, pk in enumerate(ids)}
        products = list(Product.objects.active().filter(pk__in=ids))
        products.sort(key=lambda p: preserved.get(p.pk, 999))
        return products

    def has_product(self, product_id):
        return int(product_id) in self.product_ids()

    def toggle(self, product_id):
        product_id = int(product_id)
        if self.is_authenticated:
            item = WishlistItem.objects.filter(user=self.user, product_id=product_id).first()
            if item:
                item.delete()
                return False
            WishlistItem.objects.create(user=self.user, product_id=product_id)
            return True

        ids = self._session_ids()
        if product_id in ids:
            ids.remove(product_id)
            self._save_session_ids(ids)
            return False
        ids.append(product_id)
        self._save_session_ids(ids)
        return True

    def remove(self, product_id):
        product_id = int(product_id)
        if self.is_authenticated:
            WishlistItem.objects.filter(user=self.user, product_id=product_id).delete()
            return
        ids = self._session_ids()
        if product_id in ids:
            ids.remove(product_id)
            self._save_session_ids(ids)

    def merge_session_to_user(self):
        if not self.is_authenticated:
            return
        ids = self._session_ids()
        if not ids:
            return
        for product_id in ids:
            try:
                WishlistItem.objects.get_or_create(user=self.user, product_id=product_id)
            except IntegrityError:
                pass
        self.request.session.pop(WISHLIST_SESSION_KEY, None)
        self.request.session.modified = True
