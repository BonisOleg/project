from unittest.mock import MagicMock, patch

from django.core import mail
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.test import SimpleTestCase, TestCase, override_settings

from src.core.email_backends.resend import ResendEmailBackend, _extract_bodies
from src.core.services.resend import ResendError, ResendService


class ExtractBodiesTests(SimpleTestCase):
    def test_plain_text_body(self):
        message = EmailMessage('Subj', 'plain body', 'from@example.com', ['to@example.com'])
        text, html = _extract_bodies(message)
        self.assertEqual(text, 'plain body')
        self.assertEqual(html, '')

    def test_html_alternative(self):
        message = EmailMultiAlternatives('Subj', 'plain', 'from@example.com', ['to@example.com'])
        message.attach_alternative('<p>html</p>', 'text/html')
        text, html = _extract_bodies(message)
        self.assertEqual(text, 'plain')
        self.assertEqual(html, '<p>html</p>')


class ResendServiceTests(SimpleTestCase):
    def test_requires_api_key(self):
        svc = ResendService(api_key='')
        self.assertFalse(svc.configured)
        with self.assertRaises(ResendError):
            svc.send(
                from_email='Oyra <noreply@oyra.com.ua>',
                to=['a@example.com'],
                subject='Test',
                text='Hi',
            )

    @patch('src.core.services.resend.urllib.request.urlopen')
    def test_send_success(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = b'{"id":"49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"}'
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        mock_urlopen.return_value = response

        svc = ResendService(api_key='re_test')
        result = svc.send(
            from_email='Oyra <noreply@oyra.com.ua>',
            to=['client@example.com'],
            subject='Oyra: test',
            text='Hello',
        )
        self.assertTrue(result['ok'])
        self.assertEqual(result['id'], '49a3999c-0ce1-4ea6-ab68-afcd6dc2e794')

        request = mock_urlopen.call_args[0][0]
        body = request.data.decode('utf-8')
        self.assertIn('client@example.com', body)
        self.assertIn('Bearer re_test', request.headers['Authorization'])

    @patch('src.core.services.resend.urllib.request.urlopen')
    def test_http_error_raises(self, mock_urlopen):
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            'https://api.resend.com/emails',
            422,
            'Unprocessable',
            {},
            MagicMock(read=MagicMock(return_value=b'{"message":"Invalid from"}')),
        )
        svc = ResendService(api_key='re_test')
        with self.assertRaises(ResendError) as ctx:
            svc.send(
                from_email='bad@example.com',
                to=['a@example.com'],
                subject='Test',
                text='Hi',
            )
        self.assertIn('422', str(ctx.exception))


@override_settings(
    RESEND_API_KEY='re_test',
    EMAIL_BACKEND='src.core.email_backends.resend.ResendEmailBackend',
    DEFAULT_FROM_EMAIL='Oyra <noreply@oyra.com.ua>',
)
class ResendEmailBackendTests(TestCase):
    @patch('src.core.email_backends.resend.ResendService.send')
    def test_send_mail_uses_backend(self, mock_send):
        mock_send.return_value = {'ok': True, 'id': 'abc'}
        sent = send_mail(
            'Subject',
            'Body',
            'Oyra <noreply@oyra.com.ua>',
            ['user@example.com'],
            fail_silently=False,
        )
        self.assertEqual(sent, 1)
        mock_send.assert_called_once()

    @patch('src.core.email_backends.resend.ResendService.send')
    def test_backend_send_messages(self, mock_send):
        mock_send.return_value = {'ok': True, 'id': 'abc'}
        backend = ResendEmailBackend()
        message = EmailMessage(
            'Subject',
            'Body',
            'Oyra <noreply@oyra.com.ua>',
            ['user@example.com'],
        )
        self.assertEqual(backend.send_messages([message]), 1)

    @override_settings(RESEND_API_KEY='')
    def test_missing_key_fail_silently(self):
        backend = ResendEmailBackend(fail_silently=True)
        message = EmailMessage('S', 'B', 'f@x.com', ['t@x.com'])
        self.assertEqual(backend.send_messages([message]), 0)

    @override_settings(RESEND_API_KEY='')
    def test_missing_key_raises(self):
        backend = ResendEmailBackend(fail_silently=False)
        message = EmailMessage('S', 'B', 'f@x.com', ['t@x.com'])
        with self.assertRaises(ResendError):
            backend.send_messages([message])
