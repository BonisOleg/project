from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('debug/hero-layout/', views.debug_hero_layout, name='debug_hero_layout'),
]
