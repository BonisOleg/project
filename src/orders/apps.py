from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.orders'
    label = 'orders'
    verbose_name = 'Замовлення'

    def ready(self):
        from . import signals  # noqa: F401
