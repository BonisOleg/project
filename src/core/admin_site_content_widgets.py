from __future__ import annotations

from typing import Any, Optional

from django.contrib.admin.widgets import AdminTextInputWidget, AdminTextareaWidget
from django.forms import CheckboxInput, ClearableFileInput, FileInput, Select, SelectMultiple
from unfold.widgets import INPUT_CLASSES, TEXTAREA_CLASSES

_SKIP_CLASSES = frozenset({
    'bg-white',
    'text-font-default-light',
    'border-base-200',
    'dark:bg-base-900',
    'dark:border-base-700',
    'dark:text-font-default-dark',
})

_FORCE_CLASSES = (
    'bg-base-900',
    'text-base-100',
    'border-base-700',
    'placeholder-base-400',
)


def cms_control_classes(base_classes: list[str], extra_class: str = '') -> str:
    classes = [item for item in base_classes if item not in _SKIP_CLASSES]
    classes.extend(_FORCE_CLASSES)
    if extra_class:
        for token in extra_class.split():
            if token not in _SKIP_CLASSES and token not in classes:
                classes.append(token)
    return ' '.join(classes)


class CmsAdminTextInputWidget(AdminTextInputWidget):
    def __init__(self, attrs: Optional[dict[str, Any]] = None) -> None:
        merged = dict(attrs or {})
        extra_class = merged.pop('class', '')
        super().__init__(attrs={
            **merged,
            'class': cms_control_classes(INPUT_CLASSES, extra_class),
        })


class CmsAdminTextareaWidget(AdminTextareaWidget):
    def __init__(self, attrs: Optional[dict[str, Any]] = None) -> None:
        merged = dict(attrs or {})
        extra_class = merged.pop('class', '')
        super().__init__(attrs={
            **merged,
            'class': cms_control_classes(TEXTAREA_CLASSES, extra_class),
        })


_SKIP_WIDGET_TYPES = (
    CheckboxInput,
    Select,
    SelectMultiple,
    FileInput,
    ClearableFileInput,
)


def apply_readable_widget(widget):
    try:
        from tinymce.widgets import TinyMCE
    except ImportError:
        TinyMCE = ()  # type: ignore[misc, assignment]

    if isinstance(widget, TinyMCE):
        return widget

    if isinstance(widget, _SKIP_WIDGET_TYPES):
        return widget

    attrs = getattr(widget, 'attrs', None)
    if not attrs:
        return widget

    css = attrs.get('class', '')
    if 'bg-base-900' in css and 'bg-white' not in css:
        return widget
    if 'bg-white' not in css and 'text-font-default-light' not in css:
        return widget

    merged_attrs = dict(attrs)
    if isinstance(widget, AdminTextareaWidget):
        return CmsAdminTextareaWidget(attrs=merged_attrs)
    return CmsAdminTextInputWidget(attrs=merged_attrs)
