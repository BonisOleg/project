from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from src.catalog.models import Product, ProductImage

HERO_SLIDES = (
    ('BAT374', 'trampoline.jpg'),
    ('B173', 'chair.jpg'),
    ('P9040', 'shelf.jpg'),
)


class Command(BaseCommand):
    help = 'Attach hero carousel images to catalog products (3 slides)'

    def handle(self, *args, **options):
        hero_dir = Path(settings.BASE_DIR) / 'static' / 'images' / 'hero'
        hero_dir.mkdir(parents=True, exist_ok=True)

        for sku, filename in HERO_SLIDES:
            source = hero_dir / filename
            if not source.exists():
                self.stderr.write(self.style.ERROR(f'Missing image: {source}'))
                continue

            product = Product.objects.filter(sku=sku, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'Product {sku} not found, skip'))
                continue

            image_bytes = source.read_bytes()
            buffer = BytesIO(image_bytes)

            ProductImage.objects.filter(product=product).delete()
            ProductImage.objects.create(
                product=product,
                image=ContentFile(buffer.read(), name=f'{sku.lower()}-hero.jpg'),
                alt_text=product.name,
                sort_order=0,
                is_main=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Attached: {product.name}'))

        self.stdout.write(self.style.SUCCESS('Hero gallery: 3 images ready'))
