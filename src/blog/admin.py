from django.contrib import admin
from unfold.admin import ModelAdmin

from src.core.admin_utils import ImagePreviewMixin, TinyMCEAdminMixin

from .models import Post


@admin.register(Post)
class PostAdmin(ImagePreviewMixin, TinyMCEAdminMixin, ModelAdmin):
    list_display = ('title', 'get_image_preview', 'is_published', 'published_at')
    list_filter = ('is_published',)
    list_filter_submit = True
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
    readonly_fields = ('get_image_preview', 'created_at')
    fieldsets = (
        ('Основне', {'fields': ('title', 'slug', 'excerpt', 'content', 'image', 'get_image_preview')}),
        ('Публікація', {'fields': ('is_published', 'published_at', 'created_at')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )
