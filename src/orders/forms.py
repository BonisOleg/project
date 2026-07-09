from django import forms

from .models import Order


class CheckoutStep1Form(forms.Form):
    pass


class CheckoutStep2Form(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'comment', 'create_account']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'field__input', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'field__input', 'autocomplete': 'family-name'}),
            'phone': forms.TelInput(attrs={'class': 'field__input', 'autocomplete': 'tel'}),
            'email': forms.EmailInput(attrs={'class': 'field__input', 'autocomplete': 'email'}),
            'comment': forms.Textarea(attrs={'class': 'field__input', 'rows': 3}),
            'create_account': forms.CheckboxInput(attrs={'class': 'field__checkbox'}),
        }


class CheckoutStep3Form(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'delivery_service', 'delivery_city', 'delivery_type', 'delivery_address',
        ]
        widgets = {
            'delivery_service': forms.RadioSelect(attrs={'class': 'delivery-option'}),
            'delivery_city': forms.TextInput(attrs={'class': 'field__input'}),
            'delivery_type': forms.RadioSelect(attrs={'class': 'delivery-option'}),
            'delivery_address': forms.TextInput(attrs={'class': 'field__input'}),
        }
