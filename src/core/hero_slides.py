from django.templatetags.static import static
from django.urls import reverse

from src.catalog.models import Product

HERO_SLIDE_SKUS = ('BAT374', 'B173', 'P9040')


def get_hero_slides(limit: int = 3):
    products = (
        Product.objects.active()
        .filter(sku__in=HERO_SLIDE_SKUS)
        .select_related('category', 'brand')
        .prefetch_related('images')
    )
    product_map = {product.sku: product for product in products}

    slides = []
    for sku in HERO_SLIDE_SKUS[:limit]:
        product = product_map.get(sku)
        if not product:
            continue
        image = product.main_image
        if not image:
            continue
        slides.append({
            'link_url': product.get_absolute_url(),
            'image_url': image.image.url,
            'alt': image.alt_text or product.name,
            'title': product.name,
        })

    if len(slides) >= 2:
        return slides

    catalog_url = reverse('catalog:list')
    fallback_files = ('trampoline.jpg', 'chair.jpg', 'shelf.jpg')
    fallback_alts = (
        'Батут дитячий для двору',
        'Крісло для кухні Bonro B-173 біле',
        'Стелаж металевий 180×90×40 чорний',
    )
    return [
        {
            'link_url': catalog_url,
            'image_url': static(f'images/hero/{fallback_files[index - 1]}'),
            'alt': fallback_alts[index - 1],
            'title': fallback_alts[index - 1],
        }
        for index in range(1, min(limit, len(fallback_files)) + 1)
    ]
