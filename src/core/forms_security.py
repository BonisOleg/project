"""Honeypot для публічних форм."""

from django import forms

HONEYPOT_NAME = 'company_website'


class HoneypotFormMixin:
    """Приховане поле. Заповнене значення відсікає простих ботів у view."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[HONEYPOT_NAME] = forms.CharField(
            required=False,
            label='',
            widget=forms.TextInput(attrs={
                'class': 'hp-field__input',
                'autocomplete': 'off',
                'tabindex': '-1',
                'aria-hidden': 'true',
            }),
        )


def honeypot_tripped(data) -> bool:
    if not data:
        return False
    return bool(str(data.get(HONEYPOT_NAME) or '').strip())
