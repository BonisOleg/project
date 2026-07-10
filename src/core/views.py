from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import time
from pathlib import Path


def home(request):
    from src.blog.models import Post
    from src.catalog.models import Category, Product

    from .hero_slides import get_hero_slides

    tabs = {
        'top': Product.objects.active().top_sales()[:12],
        'new': Product.objects.active().new_arrivals()[:12],
        'views': Product.objects.active().most_viewed()[:12],
    }
    tab = request.GET.get('tab', 'top')
    if tab not in tabs:
        tab = 'top'

    context = {
        'active_tab': tab,
        'tab_products': tabs[tab],
        'hero_slides': get_hero_slides(),
        'categories': Category.objects.filter(parent=None, is_active=True).order_by('sort_order')[:8],
        'blog_posts': Post.objects.published()[:3],
    }

    if request.htmx:
        return render(request, 'partials/home_products_panel.html', context)

    return render(request, 'pages/home.html', context)


def handler404(request, exception):
    from src.core.breadcrumbs import make_breadcrumbs
    return render(request, 'pages/404.html', {
        'breadcrumbs': make_breadcrumbs(('Сторінку не знайдено', '')),
    }, status=404)


def handler500(request):
    from src.core.breadcrumbs import make_breadcrumbs
    return render(request, 'pages/500.html', {
        'breadcrumbs': make_breadcrumbs(('Помилка сервера', '')),
    }, status=500)


@csrf_exempt
@require_POST
def debug_hero_layout(request):
    if not settings.DEBUG:
        return JsonResponse({'ok': False}, status=404)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False}, status=400)

    log_path = Path(settings.BASE_DIR) / '.cursor' / 'debug-0f4f88.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'sessionId': '0f4f88',
        'timestamp': int(time.time() * 1000),
        **payload,
    }
    with log_path.open('a', encoding='utf-8') as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return JsonResponse({'ok': True})
