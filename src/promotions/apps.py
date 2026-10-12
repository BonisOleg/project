from django.apps import AppConfig


class PromotionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.promotions'
    label = 'promotions'
    verbose_name = 'Промокоди'

    def ready(self):
        from . import signals  # noqa: F401
