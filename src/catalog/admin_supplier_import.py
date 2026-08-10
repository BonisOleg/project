"""Admin-форма та view для імпорту файлів постачальника."""

from __future__ import annotations

import logging

from django import forms
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse

from src.catalog.models import Category, Supplier
from src.catalog.services.supplier_import import import_supplier_file
from src.catalog.services.supplier_import_parsers import SupplierImportParseError

logger = logging.getLogger('catalog.supplier_import')

ALLOWED_EXTENSIONS = ('.csv', '.xlsx', '.json')
MAX_ERROR_ROWS_DISPLAY = 50


class SupplierImportForm(forms.Form):
    """Форма завантаження прайсу постачальника."""

    file = forms.FileField(
        label='Файл постачальника',
        help_text=(
            'Підтримується вигрузка Prom/Siker: Код_товара, Название_позиции[_укр], '
            'Цена, Наличие, Название_группы. Також .csv / .xlsx / .json.'
        ),
    )
    name_locale = forms.ChoiceField(
        label='Мова назви / опису',
        choices=(
            ('uk', 'Українська (Название_позиции_укр / Описание_укр)'),
            ('ru', 'Російська (Название_позиции / Описание)'),
        ),
        initial='uk',
        help_text=(
            'Якщо у файлі є обидві колонки — обери, яку мову записати в товар. '
            'Для повного UA і RU каталогу імпортуй двічі з різним вибором мови '
            '(або окремими файлами).'
        ),
    )
    default_category = forms.ModelChoiceField(
        label='Категорія за замовчуванням',
        queryset=Category.objects.all().order_by('name'),
        help_text=(
            'Для нових товарів, якщо «Название_группы» не збігається з категорією '
            'в каталозі Oyra.'
        ),
    )

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        name = (getattr(uploaded, 'name', '') or '').lower()
        if not name.endswith(ALLOWED_EXTENSIONS):
            raise forms.ValidationError(
                'Дозволені лише файли з розширенням .csv, .xlsx або .json.',
            )
        return uploaded


class SupplierImportAdminMixin:
    """Додає URL і view імпорту до SupplierAdmin."""

    change_form_template = 'admin/catalog/supplier/change_form.html'

    def get_urls(self):
        urls = super().get_urls()
        info = self.opts.app_label, self.opts.model_name
        custom = [
            path(
                '<path:object_id>/import/',
                self.admin_site.admin_view(self.import_view),
                name='%s_%s_import' % info,
            ),
        ]
        return custom + urls

    def import_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        supplier = get_object_or_404(Supplier, pk=object_id)
        report = None
        form = SupplierImportForm(request.POST or None, request.FILES or None)

        if request.method == 'POST' and form.is_valid():
            uploaded = form.cleaned_data['file']
            try:
                if hasattr(uploaded, 'seek'):
                    uploaded.seek(0)
                report = import_supplier_file(
                    supplier=supplier,
                    file_obj=uploaded,
                    filename=uploaded.name,
                    default_category=form.cleaned_data['default_category'],
                    name_locale=form.cleaned_data['name_locale'],
                )
            except SupplierImportParseError as exc:
                form.add_error('file', str(exc))
                logger.warning(
                    'Supplier import parse failed supplier_id=%s: %s',
                    supplier.pk,
                    exc,
                )
            else:
                messages.success(request, report.summary())
                if report.error_count:
                    messages.warning(
                        request,
                        f'Частина рядків не імпортована ({report.error_count}). '
                        'Деталі нижче.',
                    )

        context = {
            **self.admin_site.each_context(request),
            'title': f'Імпорт файлу — {supplier.name}',
            'supplier': supplier,
            'form': form,
            'report': report,
            'max_error_rows': MAX_ERROR_ROWS_DISPLAY,
            'opts': self.opts,
            'has_view_permission': self.has_view_permission(request, supplier),
            'has_change_permission': self.has_change_permission(request, supplier),
            'original': supplier,
            'media': self.media + form.media,
            'changelist_url': reverse(
                f'admin:{self.opts.app_label}_{self.opts.model_name}_changelist',
            ),
            'change_url': reverse(
                f'admin:{self.opts.app_label}_{self.opts.model_name}_change',
                args=[supplier.pk],
            ),
        }
        return render(request, 'admin/catalog/supplier/import_form.html', context)
