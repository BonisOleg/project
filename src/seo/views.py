from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET

from src.blog.models import Post
from src.catalog.models import Category, Product
from src.pages.models import StaticPage


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Product.objects.active()

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Category.objects.active()


class PostSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return Post.objects.published()


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return StaticPage.objects.filter(is_published=True)

    def location(self, obj):
        return obj.get_absolute_url()


@require_GET
def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        f'Sitemap: {request.build_absolute_uri(reverse("seo:sitemap"))}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
