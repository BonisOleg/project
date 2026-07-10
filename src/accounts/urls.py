from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.OyraLoginView.as_view(), name='login'),
    path('logout/', views.OyraLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('cabinet/', views.cabinet, name='cabinet'),
    path('profile/', views.profile, name='profile'),
    path('wishlist/', views.wishlist_page, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.wishlist_add, name='wishlist_add'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
    path('password-reset/', views.OyraPasswordResetView.as_view(), name='password_reset'),
    path(
        'password-reset/done/',
        views.OyraPasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
]
