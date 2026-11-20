from django.shortcuts import render


def home(request):
    from src.blog.models import Post
    from src.catalog.models import Category, Product

    from .hero_slides import get_hero_slides

    tabs = {
        'top': Product.objects.top_sales()[:12],
        'new': Product.objects.new_arrivals()[:12],
        'views': Product.objects.most_viewed()[:12],
    }
    tab = request.GET.get('tab', 'top')
    if tab not in tabs:
        tab = 'top'

    context = {
        'active_tab': tab,
        'tab_products': tabs[tab],
        'hero_slides': get_hero_slides(),
        'categories': Category.objects.filter(parent=None, is_active=True).order_by('sort_order'),
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
