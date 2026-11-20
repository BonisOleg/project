from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm as BasePasswordResetForm,
    UserCreationForm,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from src.core.forms_security import HoneypotFormMixin
from src.core.validators import clean_person_name, normalize_ua_phone

from .models import DeliveryAddress, User

PASSWORD_HINT = (
    'Мінімум 8 символів, хоча б одна велика літера та одна цифра.'
)


def _password_rules_ok(password: str) -> None:
    """Додаткові бізнес-правила до стандартних Django validators."""
    errors = []
    if len(password or '') < 8:
        errors.append('Пароль має містити мінімум 8 символів.')
    if not any(ch.isupper() for ch in (password or '')):
        errors.append('Додайте хоча б одну велику літеру.')
    if not any(ch.isdigit() for ch in (password or '')):
        errors.append('Додайте хоча б одну цифру.')
    if errors:
        raise ValidationError(errors)


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'field__input', 'autocomplete': 'email'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'field__input',
            'autocomplete': 'current-password',
            'data-password-toggle': '1',
        }),
    )


class PasswordResetForm(HoneypotFormMixin, BasePasswordResetForm):
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'field__input',
            'autocomplete': 'email',
            'inputmode': 'email',
            'maxlength': '254',
            'data-kind': 'email',
        }),
    )


class RegisterForm(HoneypotFormMixin, UserCreationForm):
    first_name = forms.CharField(
        min_length=2,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'field__input',
            'autocomplete': 'given-name',
            'autocapitalize': 'words',
            'minlength': '2',
            'maxlength': '100',
            'pattern': r"[A-Za-zА-Яа-яІіЇїЄєҐґ'’ \-]{2,100}",
            'data-kind': 'name',
        }),
    )
    phone = forms.CharField(
        max_length=32,
        widget=forms.TelInput(attrs={
            'class': 'field__input',
            'autocomplete': 'tel',
            'inputmode': 'tel',
            'maxlength': '22',
            'pattern': r'[0-9+() \-]{9,22}',
            'data-kind': 'phone',
        }),
    )
    agree = forms.BooleanField(label='Погоджуюсь з публічним договором')

    class Meta:
        model = User
        fields = ('first_name', 'email', 'phone', 'password1', 'password2')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'field__input',
                'autocomplete': 'email',
                'inputmode': 'email',
                'maxlength': '254',
                'data-kind': 'email',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'field__input',
            'data-password-toggle': '1',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].help_text = PASSWORD_HINT
        self.fields['password2'].widget.attrs.update({
            'class': 'field__input',
            'data-password-toggle': '1',
            'autocomplete': 'new-password',
        })

    def clean_first_name(self):
        return clean_person_name(self.cleaned_data.get('first_name'), label='Імʼя')

    def clean_phone(self):
        return normalize_ua_phone(self.cleaned_data.get('phone'))

    def clean_password1(self):
        password = self.cleaned_data.get('password1') or ''
        _password_rules_ok(password)
        validate_password(password, self.instance)
        return password


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'field__input',
                'autocomplete': 'given-name',
                'autocapitalize': 'words',
                'minlength': '2',
                'maxlength': '100',
                'pattern': r"[A-Za-zА-Яа-яІіЇїЄєҐґ'’ \-]{2,100}",
                'data-kind': 'name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'field__input',
                'autocomplete': 'family-name',
                'autocapitalize': 'words',
                'maxlength': '100',
                'pattern': r"[A-Za-zА-Яа-яІіЇїЄєҐґ'’ \-]{2,100}",
                'data-kind': 'name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'field__input',
                'autocomplete': 'email',
                'inputmode': 'email',
                'maxlength': '254',
                'data-kind': 'email',
            }),
            'phone': forms.TelInput(attrs={
                'class': 'field__input',
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'maxlength': '22',
                'pattern': r'[0-9+() \-]{9,22}',
                'data-kind': 'phone',
            }),
        }

    def clean_first_name(self):
        return clean_person_name(self.cleaned_data.get('first_name'), label='Імʼя')

    def clean_last_name(self):
        return clean_person_name(
            self.cleaned_data.get('last_name'), required=False, label='Прізвище',
        )

    def clean_phone(self):
        return normalize_ua_phone(self.cleaned_data.get('phone'), required=False)


class AddressForm(forms.ModelForm):
    class Meta:
        model = DeliveryAddress
        fields = ('label', 'city', 'address', 'is_default')
        widgets = {
            'label': forms.TextInput(attrs={'class': 'field__input'}),
            'city': forms.TextInput(attrs={'class': 'field__input'}),
            'address': forms.TextInput(attrs={'class': 'field__input'}),
        }
