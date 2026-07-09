from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_list, name='list'),
    path('sale/', views.sale_list, name='sale'),
    path('search/', views.search, name='search'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
    path('compare/', views.compare_page, name='compare'),
    path('category/<slug:slug>/', views.category_detail, name='category'),
    path('product/<slug:slug>/', views.product_detail, name='product'),
]
