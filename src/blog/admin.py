from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter

from src.core.admin_guidelines import get_image_hint
from src.core.admin_utils import ImagePreviewMixin, TinyMCEAdminMixin

from .models import Post

_BLOG_IMAGE_HINT = get_image_hint('blog')


@admin.register(Post)
class PostAdmin(ImagePreviewMixin, TinyMCEAdminMixin, ModelAdmin):
    list_display = ('title', 'get_image_preview', 'is_published', 'published_at')
    list_filter = [
        ('is_published', ChoicesDropdownFilter),
    ]
    list_filter_submit = True
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
    readonly_fields = ('get_image_preview', 'created_at')
    fieldsets = (
        ('Основне', {'fields': ('title', 'slug', 'excerpt', 'content', 'image', 'get_image_preview')}),
        ('Публікація', {'fields': ('is_published', 'published_at', 'created_at')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'image':
            field.help_text = _BLOG_IMAGE_HINT
        return field
