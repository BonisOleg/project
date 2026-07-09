from django.urls import path

from . import views

app_name = 'pages'

urlpatterns = [
    path('newsletter/', views.newsletter_subscribe, name='newsletter'),
    path('faq/', views.faq_page, name='faq'),
    path('<slug:slug>/', views.static_page, name='static'),
]
