from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from src.cart.services import CartService
from src.catalog.models import Category, Product
from src.promotions.models import PromoCode

User = get_user_model()

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


class CartPromoHelpers:
    def _seed(self):
        self.category = Category.objects.create(name='Тест кат', is_active=True)
        self.product = Product.objects.create(
            category=self.category,
            name='Тест товар',
            sku='PROMO-CART-1',
            price=Decimal('1000.00'),
            stock_quantity=10,
            is_active=True,
        )
        self.promo = PromoCode.objects.create(
            code='SAVE10',
            discount_type=PromoCode.TYPE_PERCENT,
            discount_value=Decimal('10'),
            is_active=True,
        )

    def _add_to_cart(self, client=None):
        client = client or self.client
        session = client.session
        session['oyra_cart'] = {str(self.product.pk): 1}
        session.save()


@override_settings(STORAGES=TEST_STORAGES)
class RemovePromoTests(CartPromoHelpers, TestCase):
    def setUp(self):
        self._seed()
        self._add_to_cart()

    def test_remove_promo_pops_session_and_hides_discount(self):
        session = self.client.session
        session['promo_code'] = 'SAVE10'
        session.save()

        detail = self.client.get(reverse('cart:detail'))
        self.assertContains(detail, 'SAVE10')
        self.assertContains(detail, 'Видалити промокод')

        resp = self.client.post(reverse('cart:promo_remove'))
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn('promo_code', self.client.session)

        detail2 = self.client.get(reverse('cart:detail'))
        self.assertNotContains(detail2, 'Видалити промокод')
        self.assertContains(detail2, 'placeholder="Промокод"')


@override_settings(STORAGES=TEST_STORAGES)
class ClearCartPopsPromoTests(CartPromoHelpers, TestCase):
    def setUp(self):
        self._seed()

    def test_cart_service_clear_pops_promo(self):
        session = self.client.session
        session['promo_code'] = 'SAVE10'
        session['oyra_cart'] = {str(self.product.pk): 1}
        session.save()

        request = RequestFactory().get('/')
        request.session = self.client.session
        CartService(request).clear()
        request.session.save()

        self.assertEqual(self.client.session.get('oyra_cart'), {})
        self.assertNotIn('promo_code', self.client.session)


@override_settings(STORAGES=TEST_STORAGES)
class LoginLogoutPopsPromoTests(CartPromoHelpers, TestCase):
    def setUp(self):
        self._seed()
        self.user = User.objects.create_user(
            email='promo@example.com',
            password='testpass123',
        )

    def test_login_pops_promo(self):
        session = self.client.session
        session['promo_code'] = 'SAVE10'
        session.save()
        self.assertTrue(self.client.login(email='promo@example.com', password='testpass123'))
        self.assertNotIn('promo_code', self.client.session)

    def test_logout_no_promo(self):
        self.client.login(email='promo@example.com', password='testpass123')
        session = self.client.session
        session['promo_code'] = 'SAVE10'
        session.save()
        self.client.logout()
        self.assertNotIn('promo_code', self.client.session)


class CartTemplateNoOyra15Tests(SimpleTestCase):
    def test_detail_and_promo_partial_have_no_oyra15(self):
        root = Path(__file__).resolve().parents[3]
        detail = (root / 'templates/cart/detail.html').read_text(encoding='utf-8')
        promo = (root / 'templates/cart/_cart_promo.html').read_text(encoding='utf-8')
        self.assertNotIn('OYRA15', detail)
        self.assertNotIn('OYRA15', promo)
        self.assertIn('Промокод', promo)
        self.assertIn('placeholder="Промокод"', promo)
