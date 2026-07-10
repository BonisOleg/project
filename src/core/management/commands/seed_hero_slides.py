from django.core.management.base import BaseCommand

from src.core.hero_slides import ensure_default_hero_slides
from src.core.models import HeroSlide


class Command(BaseCommand):
    help = 'Створити HeroSlide з static fallback-банерів, якщо в БД порожньо'

    def handle(self, *args, **options):
        created = ensure_default_hero_slides()
        total = HeroSlide.objects.count()
        if created:
            self.stdout.write(self.style.SUCCESS(f'Створено {created} слайдів (усього {total}).'))
        else:
            self.stdout.write(f'Слайди вже є (усього {total}), нічого не змінено.')
