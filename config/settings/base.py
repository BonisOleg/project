from pathlib import Path

from decouple import config
from django.templatetags.static import static
from django.urls import reverse_lazy

from src.core.site_content_registry import build_content_sidebar_items

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_htmx',
    'tinymce',
    'adminsortable2',
    'src.core',
    'src.catalog',
    'src.cart',
    'src.orders',
    'src.accounts',
    'src.blog',
    'src.pages',
    'src.seo',
    'src.promotions',
    'src.reviews',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'src.core.context_processors.site_context',
                'src.cart.context_processors.cart_context',
                'src.accounts.context_processors.wishlist_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uk'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:cabinet'
LOGOUT_REDIRECT_URL = 'core:home'

SESSION_COOKIE_AGE = 60 * 60 * 24 * 14

LIQPAY_PUBLIC_KEY = config('LIQPAY_PUBLIC_KEY', default='')
LIQPAY_PRIVATE_KEY = config('LIQPAY_PRIVATE_KEY', default='')
LIQPAY_SERVER_URL = config('LIQPAY_SERVER_URL', default='')
LIQPAY_SANDBOX = config('LIQPAY_SANDBOX', default=True, cast=bool)

NOVA_POSHTA_API_KEY = config('NOVA_POSHTA_API_KEY', default='')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

TINYMCE_DEFAULT_CONFIG = {
    'height': 400,
    'menubar': False,
    'plugins': 'link lists image code',
    'toolbar': 'undo redo | bold italic underline | bullist numlist | link image | code',
    'content_css': False,
    'skin': 'oxide',
}

UNFOLD = {
    'SITE_TITLE': 'Oyra Admin',
    'SITE_HEADER': 'Oyra — Адмінпанель',
    'SITE_SYMBOL': 'storefront',
    'SITE_ICON': {
        'light': lambda request: static('images/favicon/favicon-32.png'),
        'dark': lambda request: static('images/favicon/favicon-32.png'),
    },
    'SITE_FAVICONS': [
        {
            'rel': 'icon',
            'type': 'image/svg+xml',
            'href': lambda request: static('images/favicon/favicon.svg'),
        },
        {
            'rel': 'icon',
            'sizes': 'any',
            'type': 'image/x-icon',
            'href': lambda request: static('images/favicon/favicon.ico'),
        },
        {
            'rel': 'icon',
            'sizes': '32x32',
            'type': 'image/png',
            'href': lambda request: static('images/favicon/favicon-32.png'),
        },
        {
            'rel': 'apple-touch-icon',
            'sizes': '180x180',
            'type': 'image/png',
            'href': lambda request: static('images/favicon/apple-touch-icon.png'),
        },
    ],
    'SIDEBAR': {
        'show_search': True,
        'command_search': True,
        'show_all_applications': False,
        'navigation': [
            {
                'title': 'Налаштування',
                'separator': False,
                'items': [
                    {
                        'title': 'Сайт',
                        'icon': 'settings',
                        'link': reverse_lazy('admin:core_sitesettings_changelist'),
                    },
                    {
                        'title': 'Соцмережі',
                        'icon': 'share',
                        'link': reverse_lazy('admin:core_sociallink_changelist'),
                    },
                ],
            },
            {
                'title': 'Контент сторінок',
                'separator': True,
                'items': build_content_sidebar_items(),
            },
            {
                'title': 'Каталог',
                'separator': True,
                'items': [
                    {
                        'title': 'Товари',
                        'icon': 'inventory_2',
                        'link': reverse_lazy('admin:catalog_product_changelist'),
                    },
                    {
                        'title': 'Категорії',
                        'icon': 'category',
                        'link': reverse_lazy('admin:catalog_category_changelist'),
                    },
                    {
                        'title': 'Бренди',
                        'icon': 'sell',
                        'link': reverse_lazy('admin:catalog_brand_changelist'),
                    },
                    {
                        'title': 'Характеристики',
                        'icon': 'tune',
                        'link': reverse_lazy('admin:catalog_attributegroup_changelist'),
                    },
                ],
            },
            {
                'title': 'Продажі',
                'separator': True,
                'items': [
                    {
                        'title': 'Замовлення',
                        'icon': 'shopping_cart',
                        'link': reverse_lazy('admin:orders_order_changelist'),
                    },
                    {
                        'title': 'Промокоди',
                        'icon': 'local_offer',
                        'link': reverse_lazy('admin:promotions_promocode_changelist'),
                    },
                ],
            },
            {
                'title': 'Клієнти',
                'separator': True,
                'items': [
                    {
                        'title': 'Користувачі',
                        'icon': 'group',
                        'link': reverse_lazy('admin:accounts_user_changelist'),
                    },
                    {
                        'title': 'Адреси',
                        'icon': 'location_on',
                        'link': reverse_lazy('admin:accounts_deliveryaddress_changelist'),
                    },
                    {
                        'title': 'Обране',
                        'icon': 'favorite',
                        'link': reverse_lazy('admin:accounts_wishlistitem_changelist'),
                    },
                    {
                        'title': 'Підписки',
                        'icon': 'mail',
                        'link': reverse_lazy('admin:pages_newslettersubscription_changelist'),
                    },
                    {
                        'title': 'Дропшипінг',
                        'icon': 'inbox',
                        'link': reverse_lazy('admin:pages_dropshippingapplication_changelist'),
                    },
                ],
            },
            {
                'title': 'Контент',
                'separator': True,
                'items': [
                    {
                        'title': 'Блог',
                        'icon': 'newspaper',
                        'link': reverse_lazy('admin:blog_post_changelist'),
                    },
                    {
                        'title': 'Інфо-сторінки',
                        'icon': 'article',
                        'link': reverse_lazy('admin:pages_staticpage_changelist'),
                    },
                    {
                        'title': 'FAQ',
                        'icon': 'help',
                        'link': reverse_lazy('admin:pages_faqitem_changelist'),
                    },
                    {
                        'title': 'Інструкції',
                        'icon': 'description',
                        'link': reverse_lazy('admin:pages_productinstruction_changelist'),
                    },
                ],
            },
            {
                'title': 'Модерація',
                'separator': True,
                'items': [
                    {
                        'title': 'Відгуки',
                        'icon': 'reviews',
                        'link': reverse_lazy('admin:reviews_review_changelist'),
                    },
                ],
            },
        ],
    },
}

CONTENT_SECURITY_POLICY = {
    'EXCLUDE_URL_PREFIXES': ('/admin/',),
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'",),
        'style-src': ("'self'", 'https://fonts.googleapis.com'),
        'font-src': ("'self'", 'https://fonts.gstatic.com'),
        'img-src': ("'self'", 'data:', 'https:'),
        'connect-src': ("'self'",),
        'frame-src': ("'self'", 'https://www.liqpay.ua'),
        'frame-ancestors': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'src': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}

CART_SESSION_KEY = 'oyra_cart'
COMPARE_SESSION_KEY = 'oyra_compare'
COMPARE_MAX_ITEMS = 4
