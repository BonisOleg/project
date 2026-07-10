from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.admin.sites import site as default_admin_site
from django.core.cache import cache
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanWidget

from src.core.admin_site_content_widgets import CmsAdminTextInputWidget, CmsAdminTextareaWidget

from src.core.admin_guidelines import get_image_hint, get_text_limit_hint
from src.core.admin_hero_slides import build_hero_slide_formset
from src.core.block_defaults import (
    BLOCK_CONTENT_TYPES,
    BLOCK_DEFAULTS,
    INLINE_KEYS,
    MULTILINE_KEYS,
    is_visibility_key,
)
from src.core.context_processors import SITE_BLOCKS_CACHE_KEY
from src.core.models import SiteBlock, SiteSettings
from src.core.site_content_registry import (
    ContentSection,
    get_block_field_label,
    get_section,
    iter_section_blocks,
)

SECTION_VISIBLE_FIELD = 'section_visible'


def block_field_name(page: str, key: str, suffix: str) -> str:
    return f'block__{page}__{key}__{suffix}'


def _block_content_type(page: str, key: str) -> str:
    return BLOCK_CONTENT_TYPES.get((page, key), SiteBlock.ContentType.TEXT)


def _is_inline_key(key: str) -> bool:
    return key in INLINE_KEYS


def _is_multiline_key(key: str) -> bool:
    return key in MULTILINE_KEYS


def load_section_blocks(section: ContentSection) -> dict[tuple[str, str], SiteBlock]:
    blocks: dict[tuple[str, str], SiteBlock] = {}
    for page, key in iter_section_blocks(section):
        content_type = _block_content_type(page, key)
        block, _created = SiteBlock.objects.get_or_create(
            page=page,
            key=key,
            defaults={
                'label': get_block_field_label(page, key),
                'content_type': content_type,
                'text_html': BLOCK_DEFAULTS.get((page, key), '1' if is_visibility_key(key) else ''),
                'sort_order': 0,
                'is_active': True,
            },
        )
        blocks[(page, key)] = block
    return blocks


class SitePageContentForm(forms.Form):
    def __init__(
        self,
        section: ContentSection,
        blocks: dict[tuple[str, str], SiteBlock],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.section = section
        self.blocks = blocks

        if section.visibility_key:
            page, key = self._visibility_page_key(section)
            block = blocks[(page, key)]
            initial = block.text_html.strip() in {'1', 'true', 'True'}
            self.fields[SECTION_VISIBLE_FIELD] = forms.BooleanField(
                label='Показувати секцію на сайті',
                required=False,
                initial=initial,
                widget=UnfoldBooleanWidget(),
            )

        for page, key in section.blocks:
            block = blocks[(page, key)]
            self._add_block_fields(block)

    def _visibility_page_key(self, section: ContentSection) -> tuple[str, str]:
        for page, key in iter_section_blocks(section):
            if key == section.visibility_key:
                return page, key
        raise KeyError(section.visibility_key)

    def _add_block_fields(self, block: SiteBlock) -> None:
        page = block.page
        key = block.key
        field_label = get_block_field_label(page, key)

        if is_visibility_key(key) and key != self.section.visibility_key:
            initial = block.text_html.strip() in {'1', 'true', 'True'}
            self.fields[block_field_name(page, key, 'visible')] = forms.BooleanField(
                label=field_label,
                required=False,
                initial=initial,
                widget=UnfoldBooleanWidget(),
            )
            return

        if block.content_type == SiteBlock.ContentType.TEXT:
            if _is_inline_key(key):
                widget = CmsAdminTextInputWidget()
            elif _is_multiline_key(key):
                widget = CmsAdminTextareaWidget(attrs={'rows': 4})
            else:
                widget = CmsAdminTextareaWidget(attrs={'rows': 2})

            char_hint = get_text_limit_hint(key)
            self.fields[block_field_name(page, key, 'text_html')] = forms.CharField(
                label=field_label,
                initial=block.text_html,
                required=False,
                widget=widget,
                help_text=char_hint or '',
            )
            return

        if block.content_type == SiteBlock.ContentType.IMAGE:
            image_field = block_field_name(page, key, 'image')
            image_hint = get_image_hint('block_image')
            current_hint = f'Поточне: {block.image.name}. ' if block.image else ''
            self.fields[image_field] = forms.ImageField(
                label=field_label,
                required=False,
                widget=UnfoldAdminFileFieldWidget(),
                help_text=current_hint + image_hint,
            )

    def save(self) -> None:
        if SECTION_VISIBLE_FIELD in self.fields:
            page, key = self._visibility_page_key(self.section)
            block = self.blocks[(page, key)]
            block.text_html = '1' if self.cleaned_data.get(SECTION_VISIBLE_FIELD) else '0'
            block.is_active = True
            block.save()

        for block in self.blocks.values():
            page = block.page
            key = block.key
            if key == self.section.visibility_key:
                continue
            if is_visibility_key(key):
                block.text_html = '1' if self.cleaned_data.get(
                    block_field_name(page, key, 'visible'),
                ) else '0'
                block.is_active = True
                block.save()
                continue

            block.is_active = True

            if block.content_type == SiteBlock.ContentType.TEXT:
                block.text_html = self.cleaned_data.get(
                    block_field_name(page, key, 'text_html'),
                    '',
                ).strip()
            elif block.content_type == SiteBlock.ContentType.IMAGE:
                uploaded = self.cleaned_data.get(block_field_name(page, key, 'image'))
                if uploaded:
                    block.image = uploaded

            block.save()

        cache.delete(SITE_BLOCKS_CACHE_KEY)


def _bound_fields_for_keys(
    form: SitePageContentForm,
    section: ContentSection,
    keys: tuple[str, ...],
) -> list[forms.BoundField]:
    fields: list[forms.BoundField] = []
    page_keys = {key: page for page, key in section.blocks}
    for key in keys:
        page = page_keys[key]
        block = form.blocks.get((page, key))
        if block is None:
            continue
        if block.content_type == SiteBlock.ContentType.TEXT:
            if is_visibility_key(key):
                name = block_field_name(page, key, 'visible')
            else:
                name = block_field_name(page, key, 'text_html')
        else:
            name = block_field_name(page, key, 'image')
        if name in form.fields:
            fields.append(form[name])
    return fields


def _section_fieldsets(form: SitePageContentForm, section: ContentSection) -> list[tuple[str, list]]:
    fieldsets: list[tuple[str, list]] = []

    if SECTION_VISIBLE_FIELD in form.fields:
        fieldsets.append(('Видимість', [form[SECTION_VISIBLE_FIELD]]))

    if section.field_groups:
        for group in section.field_groups:
            fields = _bound_fields_for_keys(form, section, group.block_keys)
            if fields:
                fieldsets.append((group.title, fields))
    elif section.blocks:
        fields = []
        for page, key in section.blocks:
            block = form.blocks[(page, key)]
            if block.content_type == SiteBlock.ContentType.TEXT:
                if is_visibility_key(key):
                    name = block_field_name(page, key, 'visible')
                else:
                    name = block_field_name(page, key, 'text_html')
            else:
                name = block_field_name(page, key, 'image')
            if name in form.fields:
                fields.append(form[name])
        if fields:
            fieldsets.append(('', fields))

    return fieldsets


def _section_admin_change_url(section: ContentSection) -> str:
    return reverse(
        f'admin:core_{section.admin_model_name}_change',
        args=[SiteSettings.load().pk],
    )


def site_content_section_view(
    request,
    page_slug: str,
    section_slug: str,
    *,
    model_admin=None,
):
    try:
        section = get_section(page_slug, section_slug)
    except KeyError as exc:
        raise Http404 from exc

    blocks = load_section_blocks(section)
    use_hero_slides = section.slug == 'hero'
    slides_formset = None

    if request.method == 'POST':
        form = SitePageContentForm(section, blocks, request.POST, request.FILES)
        if use_hero_slides:
            slides_formset = build_hero_slide_formset(request.POST, request.FILES)
            forms_ok = form.is_valid() and slides_formset.is_valid()
        else:
            forms_ok = form.is_valid()

        if forms_ok:
            form.save()
            if slides_formset is not None:
                slides_formset.save()
            messages.success(request, f'«{section.sidebar_title or section.title}» збережено.')
            return HttpResponseRedirect(_section_admin_change_url(section))
    else:
        form = SitePageContentForm(section, blocks)
        if use_hero_slides:
            slides_formset = build_hero_slide_formset()

    opts = model_admin.model._meta if model_admin else SiteBlock._meta
    context = {
        **default_admin_site.each_context(request),
        'form': form,
        'section': section,
        'fieldsets': _section_fieldsets(form, section),
        'slides_formset': slides_formset,
        'preview_url': section.preview_url,
        'title': section.sidebar_title or section.title,
        'breadcrumb': (
            ('Контент сторінок', None),
            (section.sidebar_title or section.title, None),
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
