from decimal import Decimal

from django.conf import settings


class CartService:
    def __init__(self, request):
        self.request = request
        self.session_key = settings.CART_SESSION_KEY
        if self.session_key not in request.session:
            request.session[self.session_key] = {}

    @property
    def items(self):
        return self.request.session.get(self.session_key, {})

    def add(self, product_id, quantity=1):
        pid = str(product_id)
        cart = self.items.copy()
        cart[pid] = cart.get(pid, 0) + quantity
        self.request.session[self.session_key] = cart
        self.request.session.modified = True

    def set_quantity(self, product_id, quantity):
        pid = str(product_id)
        cart = self.items.copy()
        if quantity <= 0:
            cart.pop(pid, None)
        else:
            cart[pid] = quantity
        self.request.session[self.session_key] = cart
        self.request.session.modified = True

    def remove(self, product_id):
        self.set_quantity(product_id, 0)

    def clear(self):
        self.request.session[self.session_key] = {}
        self.request.session.modified = True

    def get_lines(self):
        from src.catalog.models import Product
        lines = []
        for pid, qty in self.items.items():
            try:
                product = Product.objects.active().get(pk=int(pid))
                lines.append({
                    'product': product,
                    'quantity': qty,
                    'line_total': product.price * qty,
                })
            except Product.DoesNotExist:
                continue
        return lines

    @property
    def count(self):
        return sum(self.items.values())

    @property
    def subtotal(self):
        return sum(line['line_total'] for line in self.get_lines())

    def apply_promo(self, code):
        from src.promotions.models import PromoCode
        try:
            promo = PromoCode.objects.get(code__iexact=code.strip(), is_active=True)
            if promo.is_valid():
                return promo
        except PromoCode.DoesNotExist:
            pass
        return None

    def total(self, promo=None):
        subtotal = self.subtotal
        if promo:
            return promo.apply_discount(subtotal)
        return subtotal
