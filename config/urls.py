from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('src.core.urls')),
    path('catalog/', include('src.catalog.urls')),
    path('cart/', include('src.cart.urls')),
    path('orders/', include('src.orders.urls')),
    path('accounts/', include('src.accounts.urls')),
    path('blog/', include('src.blog.urls')),
    path('info/', include('src.pages.urls')),
    path('', include('src.seo.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'src.core.views.handler404'
handler500 = 'src.core.views.handler500'
