from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from src.core.breadcrumbs import make_breadcrumbs
from src.core.forms_security import HoneypotFormMixin, honeypot_tripped
from src.core.rate_limit import rate_limit
from src.core.safe_redirect import safe_next
from src.core.validators import (
    clean_limited_text,
    clean_person_name,
    clean_place,
    normalize_ua_phone,
)

from .legal_pages import get_legal_page, get_related_legal_pages
from .models import DropshippingApplication, FAQItem, NewsletterSubscription, StaticPage


class NewsletterForm(HoneypotFormMixin, forms.ModelForm):
    class Meta:
        model = NewsletterSubscription
        fields = ('email',)
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'field__input',
                'placeholder': 'Ваш email',
                'autocomplete': 'email',
                'inputmode': 'email',
                'maxlength': '254',
                'data-kind': 'email',
            }),
        }


class DropshippingForm(HoneypotFormMixin, forms.ModelForm):
    class Meta:
        model = DropshippingApplication
        fields = ('name', 'phone', 'email', 'city', 'comment')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'field__input',
                'autocomplete': 'name',
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
            'city': forms.TextInput(attrs={
                'class': 'field__input',
                'autocomplete': 'address-level2',
                'autocapitalize': 'words',
                'minlength': '2',
                'maxlength': '120',
                'pattern': r"[A-Za-zА-Яа-яІіЇїЄєҐґ'’ .,()\-]{2,120}",
                'data-kind': 'place',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'field__input',
                'rows': 4,
                'maxlength': '1000',
                'data-kind': 'comment',
            }),
        }

    def clean_name(self):
        return clean_person_name(self.cleaned_data.get('name'), label='Імʼя')

    def clean_phone(self):
        return normalize_ua_phone(self.cleaned_data.get('phone'))

    def clean_city(self):
        return clean_place(self.cleaned_data.get('city'), max_len=120)

    def clean_comment(self):
        return clean_limited_text(
            self.cleaned_data.get('comment'), max_len=1000, label='Коментар',
        )


def _page_crumbs(page):
    return make_breadcrumbs((page.title, ''))


def static_page(request, slug):
    legal = get_legal_page(slug)
    if legal:
        return render(request, 'pages/legal_page.html', {
            'page': legal,
            'related_pages': get_related_legal_pages(slug),
            'breadcrumbs': make_breadcrumbs((legal['title'], '')),
        })

    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    if slug == StaticPage.SLUG_DROPSHIPPING:
        return dropshipping(request, page)
    if slug == StaticPage.SLUG_FAQ:
        return faq_page(request, page)
    if slug == StaticPage.SLUG_INSTRUCTIONS:
        return instructions(request, page)
    return render(request, 'pages/static_page.html', {
        'page': page,
        'breadcrumbs': _page_crumbs(page),
    })


def faq_page(request, page=None):
    if not page:
        page = get_object_or_404(StaticPage, slug=StaticPage.SLUG_FAQ)
    items = FAQItem.objects.filter(is_published=True)
    return render(request, 'pages/faq.html', {
        'page': page,
        'faq_items': items,
        'breadcrumbs': _page_crumbs(page),
    })


def instructions(request, page):
    from .models import ProductInstruction
    items = ProductInstruction.objects.filter(is_published=True)
    q = request.GET.get('q', '').strip()
    if q:
        items = items.filter(title__icontains=q) | items.filter(sku__icontains=q)
    return render(request, 'pages/instructions.html', {
        'page': page,
        'items': items,
        'q': q,
        'breadcrumbs': _page_crumbs(page),
    })


@rate_limit()
def dropshipping(request, page):
    if request.method == 'POST' and honeypot_tripped(request.POST):
        messages.success(request, 'Заявку надіслано. Ми звʼяжемось з вами.')
        return redirect('pages:static', slug=page.slug)
    form = DropshippingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Заявку надіслано. Ми звʼяжемось з вами.')
        return redirect('pages:static', slug=page.slug)
    return render(request, 'pages/dropshipping.html', {
        'page': page,
        'form': form,
        'breadcrumbs': _page_crumbs(page),
    })


@rate_limit()
def newsletter_subscribe(request):
    if request.method != 'POST':
        return redirect('core:home')
    if honeypot_tripped(request.POST):
        messages.success(request, 'Дякуємо за підписку! Знижку надіслано на email.')
        return redirect(safe_next(request))
    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Дякуємо за підписку! Знижку надіслано на email.')
    else:
        messages.error(request, 'Цей email вже підписаний або некоректний.')
    return redirect(safe_next(request))
