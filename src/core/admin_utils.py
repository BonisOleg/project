from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from tinymce.widgets import TinyMCE


class ImagePreviewMixin:
    image_field = 'image'
    preview_height = 80

    def get_image_preview(self, obj):
        image = getattr(obj, self.image_field, None)
        if image:
            return format_html(
                '<img src="{}" alt="" style="max-height:{}px;border-radius:8px;object-fit:cover;">',
                image.url,
                self.preview_height,
            )
        return '—'

    get_image_preview.short_description = 'Превʼю'


class TinyMCEAdminMixin:
    tinymce_fields = ('description', 'content', 'answer', 'excerpt', 'short_description')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tinymce_fields:
            kwargs['widget'] = TinyMCE()
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class SingletonModelAdminMixin:
    singleton_pk = 1

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = self.model.objects.get_or_create(pk=self.singleton_pk)
        info = self.model._meta.app_label, self.model._meta.model_name
        return HttpResponseRedirect(
            reverse(f'admin:{info[0]}_{info[1]}_change', args=[obj.pk])
        )


class ReadableUnfoldFieldsMixin:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        from src.core.admin_site_content_widgets import apply_readable_widget

        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is not None:
            formfield.widget = apply_readable_widget(formfield.widget)
        return formfield
