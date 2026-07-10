"""Структурований контент інфо/legal-сторінок."""

from django.urls import reverse

from .legal_content_info import ABOUT, DELIVERY, PAYMENT, RETURNS, SCHEDULE
from .legal_content_policy import COOKIES, OFFER, PRIVACY, SECURITY

LEGAL_PAGES = {
    'delivery': DELIVERY,
    'payment': PAYMENT,
    'returns': RETURNS,
    'about': ABOUT,
    'offer': OFFER,
    'privacy': PRIVACY,
    'cookies': COOKIES,
    'security': SECURITY,
    'schedule': SCHEDULE,
}

LEGAL_NAV_ORDER = (
    'delivery',
    'payment',
    'returns',
    'about',
    'offer',
    'schedule',
)


def _normalize_legal_section(section: dict) -> dict:
    """Завжди list для items — інакше Django template бере dict.items()."""
    return {
        'title': section.get('title', ''),
        'paragraphs': list(section.get('paragraphs') or []),
        'items': list(section.get('items') or []),
    }


def get_legal_page(slug: str) -> dict | None:
    page = LEGAL_PAGES.get(slug)
    if not page:
        return None
    sections = [_normalize_legal_section(s) for s in page.get('sections', [])]
    return {**page, 'slug': slug, 'sections': sections}


def get_related_legal_pages(current_slug: str) -> list[dict]:
    related = []
    for slug in LEGAL_NAV_ORDER:
        if slug == current_slug:
            continue
        page = LEGAL_PAGES[slug]
        related.append({
            'slug': slug,
            'title': page['title'],
            'url': reverse('pages:static', kwargs={'slug': slug}),
        })
    return related


def flatten_legal_page(page: dict) -> str:
    """Plain-text для seed / адмінки StaticPage."""
    parts = [page.get('subtitle', '').strip()]
    for section in page.get('sections', []):
        title = section.get('title', '').strip()
        if title:
            parts.append(title)
        for paragraph in section.get('paragraphs') or []:
            parts.append(paragraph.strip())
        for item in section.get('items') or []:
            parts.append(f'• {item.strip()}')
    return '\n\n'.join(p for p in parts if p)
