from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from src.core.breadcrumbs import make_breadcrumbs

from .models import DropshippingApplication, FAQItem, NewsletterSubscription, StaticPage


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscription
        fields = ('email',)
        widgets = {'email': forms.EmailInput(attrs={'class': 'field__input', 'placeholder': 'Ваш email'})}


class DropshippingForm(forms.ModelForm):
    class Meta:
        model = DropshippingApplication
        fields = ('name', 'phone', 'email', 'city', 'comment')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'field__input'}),
            'phone': forms.TelInput(attrs={'class': 'field__input'}),
            'email': forms.EmailInput(attrs={'class': 'field__input'}),
            'city': forms.TextInput(attrs={'class': 'field__input'}),
            'comment': forms.Textarea(attrs={'class': 'field__input', 'rows': 4}),
        }


def _page_crumbs(page):
    return make_breadcrumbs((page.title, ''))


def static_page(request, slug):
    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    template = 'pages/static_page.html'
    if slug == StaticPage.SLUG_DROPSHIPPING:
        return dropshipping(request, page)
    if slug == StaticPage.SLUG_FAQ:
        return faq_page(request, page)
    if slug == StaticPage.SLUG_INSTRUCTIONS:
        return instructions(request, page)
    return render(request, template, {
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


def dropshipping(request, page):
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


def newsletter_subscribe(request):
    if request.method != 'POST':
        return redirect('core:home')
    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Дякуємо за підписку! Знижку надіслано на email.')
    else:
        messages.error(request, 'Цей email вже підписаний або некоректний.')
    return redirect(request.META.get('HTTP_REFERER', '/'))
