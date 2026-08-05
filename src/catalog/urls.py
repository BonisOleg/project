from django.urls import path

from . import views
from .admin_quick_update import product_quick_update

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_list, name='list'),
    path('sale/', views.sale_list, name='sale'),
    path('search/', views.search, name='search'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
    path('compare/', views.compare_page, name='compare'),
    path('admin/product-quick-update/', product_quick_update, name='product_quick_update'),
    path('category/<slug:slug>/', views.category_detail, name='category'),
    path('product/<slug:slug>/', views.product_detail, name='product'),
]
