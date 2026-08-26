from django.test import SimpleTestCase

from src.core.utils.phone_format import phone_to_tel_uri


class PhoneFormatTests(SimpleTestCase):
    def test_local_mobile_to_e164(self):
        self.assertEqual(phone_to_tel_uri('0966821335'), '+380966821335')

    def test_second_number_is_distinct(self):
        first = phone_to_tel_uri('0966821335')
        second = phone_to_tel_uri('0731306339')
        self.assertNotEqual(first, second)
        self.assertEqual(second, '+380731306339')

    def test_already_international(self):
        self.assertEqual(phone_to_tel_uri('+380 96 682 13 35'), '+380966821335')
