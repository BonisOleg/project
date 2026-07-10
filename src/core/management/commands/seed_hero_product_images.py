from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from src.catalog.models import Product, ProductImage

# SKU → файл у static/images/hero/
PRODUCT_IMAGES = (
    ('BAT374', 'trampoline.jpg'),
    ('B173', 'chair.jpg'),
    ('B619', 'chair.jpg'),
    ('B016', 'chair.jpg'),
    ('P9040', 'shelf.jpg'),
    ('G9040', 'shelf.jpg'),
    ('SP2002', 'lounger.jpg'),
    ('VAL28', 'suitcase.jpg'),
)


class Command(BaseCommand):
    help = 'Attach seed images to catalog products'

    def handle(self, *args, **options):
        hero_dir = Path(settings.BASE_DIR) / 'static' / 'images' / 'hero'
        attached = 0

        for sku, filename in PRODUCT_IMAGES:
            source = hero_dir / filename
            if not source.exists():
                self.stderr.write(self.style.ERROR(f'Missing image: {source}'))
                continue

            product = Product.objects.filter(sku=sku, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'Product {sku} not found, skip'))
                continue

            image_bytes = source.read_bytes()
            ProductImage.objects.filter(product=product).delete()
            ProductImage.objects.create(
                product=product,
                image=ContentFile(BytesIO(image_bytes).read(), name=f'{sku.lower()}-hero.jpg'),
                alt_text=product.name,
                sort_order=0,
                is_main=True,
            )
            attached += 1
            self.stdout.write(self.style.SUCCESS(f'Attached: {product.name} ← {filename}'))

        self.stdout.write(self.style.SUCCESS(f'Product images ready: {attached}'))
