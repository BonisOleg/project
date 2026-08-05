from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm as BasePasswordResetForm,
    UserCreationForm,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

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


class PasswordResetForm(BasePasswordResetForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'field__input', 'autocomplete': 'email'}),
    )


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'field__input'}))
    phone = forms.CharField(widget=forms.TelInput(attrs={'class': 'field__input'}))
    agree = forms.BooleanField(label='Погоджуюсь з публічним договором')

    class Meta:
        model = User
        fields = ('first_name', 'email', 'phone', 'password1', 'password2')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'field__input'}),
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
            'first_name': forms.TextInput(attrs={'class': 'field__input'}),
            'last_name': forms.TextInput(attrs={'class': 'field__input'}),
            'email': forms.EmailInput(attrs={'class': 'field__input'}),
            'phone': forms.TelInput(attrs={'class': 'field__input'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = DeliveryAddress
        fields = ('label', 'city', 'address', 'is_default')
        widgets = {
            'label': forms.TextInput(attrs={'class': 'field__input'}),
            'city': forms.TextInput(attrs={'class': 'field__input'}),
            'address': forms.TextInput(attrs={'class': 'field__input'}),
        }
