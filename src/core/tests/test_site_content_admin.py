import re

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from src.core.block_defaults import is_visibility_key
from src.core.admin_site_content import load_section_blocks
from src.core.models import HeroSlide, SiteBlock, SiteSettings
from src.core.site_content_registry import get_section

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(STORAGES=TEST_STORAGES)
class SiteContentAdminTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            email='admin@test.oyra.ua',
            password='testpass123',
        )
        self.client.force_login(self.admin_user)
        SiteSettings.objects.get_or_create(pk=1)

    def test_hero_section_form_renders_readable_inputs(self):
        url = reverse('admin:core_homeherosettings_change', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Показувати секцію на сайті')
        self.assertContains(response, 'Слайди банера')
        self.assertContains(response, 'hero_slides-TOTAL_FORMS')
        self.assertContains(response, 'Додати слайд')
        self.assertNotContains(response, 'hero_image')
        self.assertEqual(HeroSlide.objects.count(), 3)
        self.assertContains(response, 'Батут дитячий для двору')
        self.assertContains(response, 'Крісло для кухні Bonro B-173 біле')
        self.assertContains(response, 'Стелаж металевий 180×90×40 чорний')

    def test_hero_title_input_has_no_bg_white(self):
        url = reverse('admin:core_homeherosettings_change', args=[1])
        response = self.client.get(url)
        html = response.content.decode()
        match = re.search(r'name="block__home__hero_title__text_html"[^>]*>', html)
        self.assertIsNotNone(match)
        self.assertIn('block__home__hero_title__text_html', match.group())

    def test_site_settings_form_uses_readable_inputs(self):
        url = reverse('admin:core_sitesettings_change', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'site_name')
        self.assertContains(response, 'name="phone"')

    def test_hero_section_save_updates_blocks(self):
        section = get_section('home', 'hero')
        blocks = load_section_blocks(section)
        payload = {
            'section_visible': 'on',
            'hero_slides-TOTAL_FORMS': '1',
            'hero_slides-INITIAL_FORMS': '0',
            'hero_slides-MIN_NUM_FORMS': '0',
            'hero_slides-MAX_NUM_FORMS': '1000',
            'hero_slides-0-alt_text': '',
            'hero_slides-0-sort_order': '0',
            'hero_slides-0-is_active': 'on',
        }
        for page, key in section.blocks:
            block = blocks[(page, key)]
            if block.content_type == 'text':
                if key == 'hero_title':
                    payload[f'block__{page}__{key}__text_html'] = 'Новий заголовок hero'
                else:
                    payload[f'block__{page}__{key}__text_html'] = block.text_html

        url = reverse('admin:core_homeherosettings_change', args=[1])
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        block = SiteBlock.objects.get(page='home', key='hero_title')
        self.assertEqual(block.text_html, 'Новий заголовок hero')
        self.assertEqual(HeroSlide.objects.count(), 0)

    def test_header_section_renders_visibility_checkboxes(self):
        url = reverse('admin:core_siteheadersettings_change', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertContains(response, 'Показувати «Каталог»')
        self.assertIn('name="block__site__header_nav_catalog_visible__visible"', html)
        self.assertNotIn('name="block__site__header_nav_catalog_visible__text_html"', html)

    def test_header_section_save_toggles_catalog_visibility(self):
        section = get_section('site', 'header')
        blocks = load_section_blocks(section)
        payload = {}
        for page, key in section.blocks:
            block = blocks[(page, key)]
            if is_visibility_key(key):
                if key == 'header_nav_catalog_visible':
                    continue
                if block.text_html.strip() in {'1', 'true', 'True'}:
                    payload[f'block__{page}__{key}__visible'] = 'on'
            elif block.content_type == 'text':
                payload[f'block__{page}__{key}__text_html'] = block.text_html

        url = reverse('admin:core_siteheadersettings_change', args=[1])
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 302)
        block = SiteBlock.objects.get(page='site', key='header_nav_catalog_visible')
        self.assertEqual(block.text_html, '0')
