from django import forms

from src.core.forms_security import HoneypotFormMixin
from src.core.validators import (
    clean_limited_text,
    clean_person_name,
    clean_place,
    normalize_ua_phone,
)

from .models import Order


class CheckoutStep1Form(forms.Form):
    pass


class CheckoutStep2Form(HoneypotFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'comment', 'create_account']
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
                'minlength': '2',
            'maxlength': '100',
            'pattern': r"[A-Za-zА-Яа-яІіЇїЄєҐґ'’ \-]{2,100}",
            'data-kind': 'name',
            }),
            'phone': forms.TelInput(attrs={
                'class': 'field__input',
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'maxlength': '22',
                'pattern': r'[0-9+() \-]{9,22}',
                'data-kind': 'phone',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'field__input',
                'autocomplete': 'email',
                'inputmode': 'email',
                'maxlength': '254',
                'data-kind': 'email',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'field__input',
                'rows': 3,
                'maxlength': '1000',
                'data-kind': 'comment',
            }),
            'create_account': forms.CheckboxInput(attrs={
                'class': 'field__checkbox',
                'id': 'id_create_account',
            }),
        }
        labels = {
            'create_account': 'Створити акаунт для швидших покупок',
        }

    def clean_first_name(self):
        return clean_person_name(self.cleaned_data.get('first_name'), label='Імʼя')

    def clean_last_name(self):
        return clean_person_name(self.cleaned_data.get('last_name'), label='Прізвище')

    def clean_phone(self):
        return normalize_ua_phone(self.cleaned_data.get('phone'))

    def clean_comment(self):
        return clean_limited_text(
            self.cleaned_data.get('comment'), max_len=1000, label='Коментар',
        )


class CheckoutStep3Form(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'delivery_service', 'delivery_city', 'delivery_type', 'delivery_address',
        ]
        widgets = {
            'delivery_service': forms.RadioSelect(attrs={'class': 'delivery-option__input'}),
            'delivery_city': forms.TextInput(attrs={
                'class': 'field__input',
                'autocomplete': 'off',
                'autocapitalize': 'words',
                'id': 'id_delivery_city',
                'minlength': '2',
                'maxlength': '150',
                'pattern': r"[A-Za-zА-Яа-яІіЇїЄєҐґ'’ .,()\-]{2,150}",
                'data-kind': 'place',
            }),
            'delivery_type': forms.RadioSelect(attrs={'class': 'delivery-option__input'}),
            'delivery_address': forms.TextInput(attrs={
                'class': 'field__input',
                'autocomplete': 'off',
                'id': 'id_delivery_address',
                'maxlength': '255',
                'data-kind': 'address',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['delivery_service'].choices = Order.DELIVERY_CHOICES_CHECKOUT
        self.fields['delivery_type'].choices = Order.NP_TYPE_CHOICES
        self.fields['delivery_type'].required = False
        if not self.is_bound and not (self.initial.get('delivery_type') or getattr(self.instance, 'delivery_type', '')):
            self.initial['delivery_type'] = Order.NP_WAREHOUSE

    def clean_delivery_city(self):
        return clean_place(self.cleaned_data.get('delivery_city'), max_len=150)

    def clean_delivery_address(self):
        return clean_limited_text(
            self.cleaned_data.get('delivery_address'),
            max_len=255,
            label='Адреса',
        )

    def clean(self):
        cleaned = super().clean()
        service = cleaned.get('delivery_service')
        city = (cleaned.get('delivery_city') or '').strip()
        address = (cleaned.get('delivery_address') or '').strip()
        delivery_type = cleaned.get('delivery_type') or ''

        if not city and 'delivery_city' not in self.errors:
            self.add_error('delivery_city', 'Оберіть або введіть місто')
        if not address and 'delivery_address' not in self.errors:
            self.add_error('delivery_address', 'Вкажіть відділення або адресу')

        if service == Order.DELIVERY_NP:
            if not delivery_type:
                self.add_error('delivery_type', 'Оберіть тип доставки')
            elif delivery_type == Order.NP_COURIER and len(address) < 5:
                self.add_error('delivery_address', 'Вкажіть повну адресу для курʼєра')
        elif service == Order.DELIVERY_COURIER:
            cleaned['delivery_type'] = ''
            if len(address) < 5:
                self.add_error('delivery_address', 'Вкажіть повну адресу для курʼєра')
        elif service == Order.DELIVERY_UP:
            cleaned['delivery_type'] = ''

        cleaned['delivery_city'] = city
        cleaned['delivery_address'] = address
        return cleaned


class CheckoutPaymentForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.RadioSelect(attrs={'class': 'delivery-option__input'}),
        }

    def clean_payment_method(self):
        method = self.cleaned_data.get('payment_method')
        if method not in dict(Order.PAYMENT_CHOICES):
            raise forms.ValidationError('Оберіть спосіб оплати')
        return method
