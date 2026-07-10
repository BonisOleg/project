from django.templatetags.static import static
from django.urls import reverse

from src.core.models import HeroSlide

_FALLBACK_FILES = ('trampoline.jpg', 'chair.jpg', 'shelf.jpg')
_FALLBACK_ALTS = (
    'Батут дитячий для двору',
    'Крісло для кухні Bonro B-173 біле',
    'Стелаж металевий 180×90×40 чорний',
)


def get_hero_slides():
    catalog_url = reverse('catalog:list')
    slides = []

    for slide in HeroSlide.objects.filter(is_active=True).exclude(image=''):
        slides.append({
            'link_url': catalog_url,
            'image_url': slide.image.url,
            'alt': slide.alt_text or '',
            'title': slide.alt_text or '',
        })

    if slides:
        return slides

    return [
        {
            'link_url': catalog_url,
            'image_url': static(f'images/hero/{_FALLBACK_FILES[index]}'),
            'alt': _FALLBACK_ALTS[index],
            'title': _FALLBACK_ALTS[index],
        }
        for index in range(len(_FALLBACK_FILES))
    ]
