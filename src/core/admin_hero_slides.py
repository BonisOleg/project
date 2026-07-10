from __future__ import annotations

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanWidget

from src.core.admin_guidelines import get_image_hint
from src.core.admin_site_content_widgets import CmsAdminTextInputWidget
from src.core.models import HeroSlide

_HERO_IMAGE_HINT = get_image_hint('hero')


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = ('image', 'alt_text', 'sort_order', 'is_active')
        widgets = {
            'image': UnfoldAdminFileFieldWidget(),
            'alt_text': CmsAdminTextInputWidget(),
            'sort_order': forms.HiddenInput(),
            'is_active': UnfoldBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['image'].help_text = _HERO_IMAGE_HINT
        self.fields['alt_text'].required = False
        self.fields['is_active'].required = False
        if not self.instance.pk:
            self.fields['is_active'].initial = True

    def _has_image(self, cleaned: dict) -> bool:
        if cleaned.get('image'):
            return True
        return bool(self.instance.pk and self.instance.image)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('DELETE'):
            return cleaned
        alt = (cleaned.get('alt_text') or '').strip()
        if not self._has_image(cleaned) and alt:
            self.add_error('image', 'Завантажте фото для слайда.')
        return cleaned


class HeroSlideBaseFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        order = 0
        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            if not form._has_image(form.cleaned_data):
                continue
            form.cleaned_data['sort_order'] = order
            form.instance.sort_order = order
            order += 1

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        saved = []
        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE'):
                if form.instance.pk:
                    form.instance.delete()
                continue
            if not form._has_image(form.cleaned_data):
                continue
            saved.append(form.save(commit=True))
        return saved


HeroSlideFormSet = modelformset_factory(
    HeroSlide,
    form=HeroSlideForm,
    formset=HeroSlideBaseFormSet,
    extra=1,
    can_delete=True,
)


def build_hero_slide_formset(data=None, files=None) -> HeroSlideFormSet:
    if data is None and files is None:
        from src.core.hero_slides import ensure_default_hero_slides

        ensure_default_hero_slides()
    queryset = HeroSlide.objects.all()
    if data is None and files is None:
        return HeroSlideFormSet(queryset=queryset, prefix='hero_slides')
    return HeroSlideFormSet(data, files, queryset=queryset, prefix='hero_slides')
