"""Адмінка реквізитів ФОП для сторінки публічного договору (оферти)."""

from __future__ import annotations

from dataclasses import dataclass

from django import forms
from django.contrib import messages
from django.contrib.admin.sites import site as default_admin_site
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from src.core.admin_site_content_widgets import CmsAdminTextInputWidget
from src.core.models import SiteSettings


@dataclass(frozen=True)
class OfferRequisitesSection:
    title: str = 'Оферта — Реквізити'
    sidebar_title: str = 'Оферта — Реквізити'
    description: str = (
        'Реквізити ФОП для розділу «Реквізити та контакти» у публічному договорі. '
        'Ті самі дані використовуються при безготівковій оплаті в кошику.'
    )
    preview_url: str = '/offer/'


OFFER_REQUISITES_SECTION = OfferRequisitesSection()

OFFER_REQUISITES_FIELDS: tuple[tuple[str, str], ...] = (
    ('bank_recipient', 'Отримувач (ФОП/ТОВ)'),
    ('bank_iban', 'Рахунок отримувача (IBAN)'),
    ('bank_edrpou', 'ЄДРПОУ / ІПН'),
    ('bank_name', 'Банк'),
)


class OfferRequisitesForm(forms.Form):
    def __init__(self, settings_obj: SiteSettings, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, label in OFFER_REQUISITES_FIELDS:
            max_lengths = {
                'bank_iban': 34,
                'bank_edrpou': 20,
            }
            self.fields[field_name] = forms.CharField(
                label=label,
                initial=getattr(settings_obj, field_name, ''),
                required=False,
                max_length=max_lengths.get(field_name, 255),
                widget=CmsAdminTextInputWidget(),
            )

    def save(self, settings_obj: SiteSettings) -> None:
        for field_name, _label in OFFER_REQUISITES_FIELDS:
            value = self.cleaned_data.get(field_name, '')
            setattr(settings_obj, field_name, value.strip())
        settings_obj.save()


def offer_requisites_admin_view(request, *, model_admin=None):
    settings_obj = SiteSettings.load()
    section = OFFER_REQUISITES_SECTION

    if request.method == 'POST':
        form = OfferRequisitesForm(settings_obj, request.POST)
        if form.is_valid():
            form.save(settings_obj)
            messages.success(request, f'«{section.sidebar_title}» збережено.')
            return HttpResponseRedirect(
                reverse('admin:core_offerrequisitessettings_change', args=[settings_obj.pk]),
            )
    else:
        form = OfferRequisitesForm(settings_obj)

    fieldsets = [
        ('Реквізити ФОП', [form[field_name] for field_name, _label in OFFER_REQUISITES_FIELDS]),
    ]

    opts = model_admin.model._meta if model_admin else SiteSettings._meta
    context = {
        **default_admin_site.each_context(request),
        'form': form,
        'section': section,
        'fieldsets': fieldsets,
        'slides_formset': None,
        'preview_url': section.preview_url,
        'title': section.sidebar_title,
        'breadcrumb': (
            ('Контент сторінок', None),
            (section.sidebar_title, None),
        ),
        'opts': opts,
        'has_view_permission': True,
        'add': False,
        'change': True,
        'is_popup': False,
        'save_as': False,
        'show_save': True,
        'show_save_and_continue': False,
        'show_save_and_add_another': False,
        'show_delete': False,
    }
    return render(request, 'admin/core/site_content_page.html', context)
