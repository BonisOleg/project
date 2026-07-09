from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm as BasePasswordResetForm, UserCreationForm

from .models import DeliveryAddress, User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'field__input', 'autocomplete': 'email'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'field__input', 'autocomplete': 'current-password'}),
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
        self.fields['password1'].widget.attrs['class'] = 'field__input'
        self.fields['password2'].widget.attrs['class'] = 'field__input'


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
