from decimal import Decimal

from django.urls import reverse

from src.orders.models import Order
from src.orders.services.pricing import is_on_sale, price_cart
from src.orders.tests.test_pricing_consistency import PricingConsistencyTests
from src.promotions.models import PromoCode


class PromoSaleExclusionTests(PricingConsistencyTests):
    """Промокод не діє на акційні товари (old_price > price)."""

    def _promo(self, code, kind, value):
        return PromoCode.objects.create(
            code=code, discount_type=kind, discount_value=Decimal(value), is_active=True,
        )

    def _checkout_order(self):
        self.client.get(reverse('orders:checkout_step', kwargs={'step': 1}))
        return Order.objects.get(pk=self.client.session['checkout_order_id'])

    def test_is_on_sale_rule(self):
        self.assertTrue(is_on_sale(self._product('S-1', Decimal('900'), Decimal('1000'))))
        self.assertFalse(is_on_sale(self._product('S-2', Decimal('1734'), Decimal('1574'))))
        self.assertFalse(is_on_sale(self._product('S-3', Decimal('1000'))))

    def test_mixed_cart_percent_only_regular_lines(self):
        regular = self._product('MIX-R', Decimal('1574.00'))
        sale = self._product('MIX-S', Decimal('1000.00'), Decimal('1500.00'))
        promo = self._promo('PCT15', PromoCode.TYPE_PERCENT, '15')
        cart = self._cart([(regular, 1), (sale, 2)], promo_code=promo.code)
        pricing = price_cart(cart, promo)
        self.assertEqual(pricing.subtotal, Decimal('3574.00'))
        self.assertEqual(pricing.eligible_subtotal, Decimal('1574.00'))
        self.assertEqual(pricing.discount, Decimal('236.10'))
        self.assertEqual(pricing.total, Decimal('3337.90'))
        self.assertTrue(pricing.promo_excludes_sale_items)

        page = self.client.get(reverse('cart:detail'))
        self.assertEqual(page.context['discount_amount'], pricing.discount)
        self.assertEqual(page.context['total'], pricing.total)
        self.assertContains(page, 'Промокод не діє на акційні товари')

        order = self._checkout_order()
        self.assertEqual(order.discount, pricing.discount)
        self.assertEqual(order.total, pricing.total)
        self.assertEqual(self._liqpay_amount(order), Decimal('3337.90'))

    def test_all_sale_cart_zero_discount_with_note(self):
        sale = self._product('ALL-S', Decimal('800.00'), Decimal('1000.00'))
        promo = self._promo('FIX100', PromoCode.TYPE_FIXED, '100')
        cart = self._cart([(sale, 1)], promo_code=promo.code)
        pricing = price_cart(cart, promo)
        self.assertEqual(pricing.eligible_subtotal, Decimal('0.00'))
        self.assertEqual(pricing.discount, Decimal('0.00'))
        self.assertEqual(pricing.total, Decimal('800.00'))

        page = self.client.get(reverse('cart:detail'))
        self.assertContains(page, 'Промокод не діє на акційні товари')
        order = self._checkout_order()
        self.assertEqual(order.discount, Decimal('0.00'))
        self.assertEqual(order.total, Decimal('800.00'))
        self.assertEqual(self._liqpay_amount(order), Decimal('800.00'))

    def test_fixed_capped_at_eligible_subtotal(self):
        regular = self._product('CAP-R', Decimal('50.00'))
        sale = self._product('CAP-S', Decimal('900.00'), Decimal('1200.00'))
        promo = self._promo('FIX500', PromoCode.TYPE_FIXED, '500')
        cart = self._cart([(regular, 1), (sale, 1)], promo_code=promo.code)
        pricing = price_cart(cart, promo)
        self.assertEqual(pricing.discount, Decimal('50.00'))
        self.assertEqual(pricing.total, Decimal('900.00'))

    def test_percent_half_up_rounding_on_eligible(self):
        regular = self._product('RND-R', Decimal('10.05'))
        sale = self._product('RND-S', Decimal('5.00'), Decimal('7.00'))
        promo = self._promo('PCT50', PromoCode.TYPE_PERCENT, '50')
        pricing = price_cart(self._cart([(regular, 1), (sale, 1)], promo_code=promo.code), promo)
        self.assertEqual(pricing.discount, Decimal('5.03'))
        self.assertEqual(pricing.total, Decimal('10.02'))

    def test_no_sale_lines_no_note(self):
        regular = self._product('NN-R', Decimal('1000.00'))
        promo = self._promo('PCT10', PromoCode.TYPE_PERCENT, '10')
        self._cart([(regular, 1)], promo_code=promo.code)
        page = self.client.get(reverse('cart:detail'))
        self.assertNotContains(page, 'Промокод не діє на акційні товари')
        self.assertEqual(page.context['discount_amount'], Decimal('100.00'))
