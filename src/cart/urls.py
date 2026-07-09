from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('add/<int:product_id>/', views.cart_add, name='add'),
    path('update/<int:product_id>/', views.cart_update, name='update'),
    path('remove/<int:product_id>/', views.cart_remove, name='remove'),
    path('promo/', views.apply_promo, name='promo'),
    path('mini/', views.mini_cart, name='mini'),
    path('compare/add/<int:product_id>/', views.compare_add, name='compare_add'),
    path('compare/remove/<int:product_id>/', views.compare_remove, name='compare_remove'),
]
