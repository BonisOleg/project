from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from src.core.client_ip import client_ip
from src.core.validators import (
    clean_limited_text,
    clean_person_name,
    clean_place,
    normalize_ua_phone,
)
from src.orders.forms import CheckoutStep2Form
from src.pages.models import NewsletterSubscription

User = get_user_model()

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


class ValidatorTests(SimpleTestCase):
    def test_phone_ua_formats(self):
        self.assertEqual(normalize_ua_phone('+380 50 111 22 33'), '+380501112233')
        self.assertEqual(normalize_ua_phone('0501112233'), '+380501112233')
        self.assertEqual(normalize_ua_phone('501112233'), '+380501112233')

    def test_phone_rejects_letters(self):
        with self.assertRaises(ValidationError):
            normalize_ua_phone('05011122ab')

    def test_name_rejects_digits(self):
        with self.assertRaises(ValidationError):
            clean_person_name('Іван1')

    def test_name_accepts_hyphen_and_apostrophe(self):
        self.assertEqual(clean_person_name("Мар'ян-Ігор"), "Мар'ян-Ігор")

    def test_comment_max_length(self):
        with self.assertRaises(ValidationError):
            clean_limited_text('я' * 1001, max_len=1000)

    def test_place_allows_nova_poshta_label(self):
        self.assertEqual(
            clean_place('м. Київ, Київська обл.'),
            'м. Київ, Київська обл.',
        )


class CheckoutContactFormTests(SimpleTestCase):
    def test_phone_is_normalized(self):
        form = CheckoutStep2Form(data={
            'first_name': 'Олена',
            'last_name': 'Коваль',
            'phone': '050 111 22 33',
            'email': 'olena@example.com',
            'comment': 'Коротко',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['phone'], '+380501112233')


@override_settings(STORAGES=TEST_STORAGES, RATE_LIMIT_ENABLED=True)
class PublicFormSecurityTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_newsletter_honeypot_does_not_save(self):
        response = self.client.post(reverse('pages:newsletter'), {
            'email': 'bot@example.com',
            'company_website': 'https://spam.test',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            NewsletterSubscription.objects.filter(email='bot@example.com').exists(),
        )

    def test_newsletter_external_referer_stays_on_site(self):
        response = self.client.post(
            reverse('pages:newsletter'),
            {'email': 'reader@example.com'},
            HTTP_REFERER='https://evil.example/phish',
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.example', response['Location'])
        self.assertTrue(
            NewsletterSubscription.objects.filter(email='reader@example.com').exists(),
        )

    def test_newsletter_same_host_referer_is_kept(self):
        response = self.client.post(
            reverse('pages:newsletter'),
            {'email': 'back@example.com'},
            HTTP_REFERER='http://testserver/cart/',
        )
        self.assertEqual(response['Location'], 'http://testserver/cart/')

    def test_newsletter_sixth_post_is_limited(self):
        url = reverse('pages:newsletter')
        for index in range(5):
            response = self.client.post(url, {'email': f'user{index}@example.com'})
            self.assertEqual(response.status_code, 302)
        blocked = self.client.post(url, {'email': 'user6@example.com'})
        self.assertEqual(blocked.status_code, 429)
        self.assertFalse(
            NewsletterSubscription.objects.filter(email='user6@example.com').exists(),
        )

    def test_register_honeypot_does_not_create_user(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Олена',
            'email': 'bot-reg@example.com',
            'phone': '+380501112233',
            'password1': 'Secret123',
            'password2': 'Secret123',
            'agree': 'on',
            'company_website': 'filled',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(email='bot-reg@example.com').exists())

    def test_client_ip_prefers_x_real_ip(self):
        request = RequestFactory().get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '1.2.3.4'
        request.META['HTTP_X_REAL_IP'] = '5.6.7.8'
        request.META['REMOTE_ADDR'] = '9.9.9.9'
        self.assertEqual(client_ip(request), '5.6.7.8')
