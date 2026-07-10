"""
Dropdown-фільтри Unfold з короткими українськими підписами (без «За …»).
"""
from __future__ import annotations

from collections.abc import Generator
from typing import Any

from django.contrib.admin.views.main import ChangeList
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RelatedDropdownFilter


class UkChoicesDropdownFilter(ChoicesDropdownFilter):
    """ChoicesDropdownFilter з чистим підписом поля."""

    all_option = ['', 'Всі']

    def choices(self, changelist: ChangeList) -> Generator[dict[str, Any], None, None]:
        choices = [self.all_option, *self.field.flatchoices]
        yield {
            'form': self.form_class(
                label=str(self.title).strip().capitalize(),
                name=self.lookup_kwarg,
                choices=choices,
                data={self.lookup_kwarg: self.value() or ''},
                multiple=self.multiple if hasattr(self, 'multiple') else False,
            ),
        }


class UkRelatedDropdownFilter(RelatedDropdownFilter):
    """RelatedDropdownFilter з чистим підписом поля."""

    all_option = ['', 'Всі']

    def choices(self, changelist: ChangeList) -> Generator[dict[str, Any], None, None]:
        add_facets = changelist.add_facets
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None

        if add_facets:
            choices = [self.all_option]
            for pk_val, val in self.lookup_choices:
                count = facet_counts[f'{pk_val}__c']
                choices.append((pk_val, f'{val} ({count})'))
        else:
            choices = [self.all_option, *self.lookup_choices]

        yield {
            'form': self.form_class(
                label=str(self.title).strip().capitalize(),
                name=self.lookup_kwarg,
                choices=choices,
                data={self.lookup_kwarg: self.value() or ''},
                multiple=self.multiple if hasattr(self, 'multiple') else False,
            ),
        }


class DropdownFiltersMixin:
    """Фільтри зверху над таблицею, без бічної панелі."""

    list_filter_sheet = False
    list_filter_submit = True
