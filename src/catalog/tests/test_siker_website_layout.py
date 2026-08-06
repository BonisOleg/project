from django.test import TestCase

from src.catalog.models import Category
from src.catalog.siker_website_layout import (
    EXT_BUDIV,
    EXT_DIM,
    EXT_DYTYACHI_ROOT,
    EXT_KRISLA,
    EXT_SPORT,
    apply_siker_website_layout,
)


class SikerWebsiteLayoutTests(TestCase):
    def setUp(self):
        self.dim = Category.objects.create(
            name='Дім і сад', slug='dim', external_id=EXT_DIM, sort_order=1,
        )
        self.sport = Category.objects.create(
            name='Спорт і відпочинок', slug='sport', external_id=EXT_SPORT,
        )
        self.krisla = Category.objects.create(
            name='Крісла', slug='krisla', external_id=EXT_KRISLA, parent=self.dim,
        )
        self.budiv = Category.objects.create(
            name='Будівництво і ремонт', slug='budiv',
            external_id=EXT_BUDIV, parent=self.dim,
        )
        self.cars = Category.objects.create(
            name='Дитячі електромобілі', slug='cars',
            external_id='23326876', parent=self.dim,
        )
        self.sup = Category.objects.create(
            name='SUP-дошка для плавання', slug='sup',
            external_id='23326949', parent=self.dim,
        )
        self.scooters = Category.objects.create(
            name='Самокати', slug='scooters',
            external_id='23326952', parent=self.dim,
        )
        self.carts = Category.objects.create(
            name='Візки', slug='vizky',
            external_id='23326860', parent=self.dim,
        )

    def test_layout_matches_siker_menu_roots(self):
        apply_siker_website_layout()

        self.krisla.refresh_from_db()
        self.budiv.refresh_from_db()
        self.cars.refresh_from_db()
        self.sup.refresh_from_db()
        self.scooters.refresh_from_db()
        self.carts.refresh_from_db()

        self.assertIsNone(self.krisla.parent_id)
        self.assertIsNone(self.budiv.parent_id)

        dytyachi = Category.objects.get(external_id=EXT_DYTYACHI_ROOT)
        self.assertEqual(self.cars.parent_id, dytyachi.pk)
        self.assertEqual(self.sup.parent_id, self.sport.pk)
        self.assertEqual(self.sup.name, 'Sup-дошки')
        self.assertEqual(self.scooters.parent_id, self.sport.pk)
        self.assertEqual(self.carts.parent_id, self.budiv.pk)
        self.assertEqual(self.carts.name, 'Складські візки')
