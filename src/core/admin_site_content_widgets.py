from __future__ import annotations

from typing import Any, Optional

from django.contrib.admin.widgets import AdminTextInputWidget, AdminTextareaWidget
from unfold.widgets import INPUT_CLASSES, TEXTAREA_CLASSES


def _join_classes(base_classes: list[str], extra_class: str = '') -> str:
    classes = list(base_classes)
    if extra_class:
        for token in extra_class.split():
            if token and token not in classes:
                classes.append(token)
    return ' '.join(classes)


class CmsAdminTextInputWidget(AdminTextInputWidget):
    """Текстове поле CMS — світла тема за замовчуванням, dark: для темної."""

    def __init__(self, attrs: Optional[dict[str, Any]] = None) -> None:
        merged = dict(attrs or {})
        extra_class = merged.pop('class', '')
        super().__init__(attrs={
            **merged,
            'class': _join_classes(INPUT_CLASSES, extra_class),
        })


class CmsAdminTextareaWidget(AdminTextareaWidget):
    """Багаторядкове поле CMS — світла тема за замовчуванням, dark: для темної."""

    def __init__(self, attrs: Optional[dict[str, Any]] = None) -> None:
        merged = dict(attrs or {})
        extra_class = merged.pop('class', '')
        super().__init__(attrs={
            **merged,
            'class': _join_classes(TEXTAREA_CLASSES, extra_class),
        })


def apply_readable_widget(widget):
    """Залишає стандартні Unfold-віджети (світла тема + dark: варіанти)."""
    return widget
