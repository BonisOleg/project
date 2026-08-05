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
            'create_account': forms.CheckboxInput(attrs={
                'class': 'field__checkbox',
                'id': 'id_create_account',
            }),
        }
        labels = {
            'create_account': 'Створити акаунт для швидших покупок',
        }


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
                'id': 'id_delivery_city',
            }),
            'delivery_type': forms.RadioSelect(attrs={'class': 'delivery-option__input'}),
            'delivery_address': forms.TextInput(attrs={
                'class': 'field__input',
                'autocomplete': 'off',
                'id': 'id_delivery_address',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['delivery_service'].choices = Order.DELIVERY_CHOICES_CHECKOUT

    def clean(self):
        cleaned = super().clean()
        service = cleaned.get('delivery_service')
        city = (cleaned.get('delivery_city') or '').strip()
        address = (cleaned.get('delivery_address') or '').strip()
        delivery_type = cleaned.get('delivery_type') or ''

        if not city:
            self.add_error('delivery_city', 'Оберіть або введіть місто')
        if not address:
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
