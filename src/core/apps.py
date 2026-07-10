from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.core'
    label = 'core'
    verbose_name = 'Налаштування'

    def ready(self):
        from . import signals  # noqa: F401
