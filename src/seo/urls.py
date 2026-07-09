from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .views import CategorySitemap, PostSitemap, ProductSitemap, StaticSitemap

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'posts': PostSitemap,
    'pages': StaticSitemap,
}

app_name = 'seo'

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', views.robots_txt, name='robots'),
]
