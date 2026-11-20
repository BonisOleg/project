from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(STORAGES=TEST_STORAGES, AXES_ENABLED=True)
class LoginLockoutTests(TestCase):
    def test_fifth_failure_is_blocked(self):
        User.objects.create_user(email='lock@example.com', password='Secret123')
        url = reverse('accounts:login')
        last = None
        for _ in range(5):
            last = self.client.post(url, {
                'username': 'lock@example.com',
                'password': 'wrong-pass-1',
            })
        self.assertIsNotNone(last)
        self.assertEqual(last.status_code, 429)
        blocked = self.client.post(url, {
            'username': 'lock@example.com',
            'password': 'Secret123',
        })
        self.assertEqual(blocked.status_code, 429)
