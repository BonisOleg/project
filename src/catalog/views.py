from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from .filters import ProductFilter
from .models import Brand, Category, Product


def _product_list_context(request, base_qs, page_title, breadcrumbs, category=None):
    filtered = ProductFilter(base_qs.annotate_rating(), request.GET).apply()
    paginator = Paginator(filtered, 12)
    page = paginator.get_page(request.GET.get('page'))
    context = {
        'products': page,
        'page_obj': page,
        'page_title': page_title,
        'breadcrumbs': breadcrumbs,
        'category': category,
        'brands': Brand.objects.filter(is_active=True),
        'root_categories': Category.objects.filter(parent=None, is_active=True),
        'view_mode': request.GET.get('view', 'grid'),
        'query_string': request.GET.urlencode(),
    }
    if request.htmx:
        return render(request, 'catalog/_product_grid.html', context)
    return render(request, 'catalog/list.html', context)


def catalog_list(request):
    qs = Product.objects.active().with_category()
    breadcrumbs = [{'title': 'Головна', 'url': '/'}, {'title': 'Каталог', 'url': ''}]
    return _product_list_context(request, qs, 'Усі товари', breadcrumbs)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    ids = category.get_descendant_ids()
    qs = Product.objects.active().with_category().filter(category_id__in=ids)
    crumbs = [{'title': 'Головна', 'url': '/'}, {'title': 'Каталог', 'url': '/catalog/'}]
    if category.parent:
        crumbs.append({'title': category.parent.name, 'url': category.parent.get_absolute_url()})
    crumbs.append({'title': category.name, 'url': ''})
    return _product_list_context(
        request, qs, category.meta_title or category.name, crumbs, category,
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.active().with_category().annotate_rating(), slug=slug,
    )
    product.increment_views()
    similar = Product.objects.active().filter(
        category=product.category,
    ).exclude(pk=product.pk)[:4]
    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'similar_products': similar,
        'breadcrumbs': [
            {'title': 'Головна', 'url': '/'},
            {'title': 'Каталог', 'url': '/catalog/'},
            {'title': product.category.name, 'url': product.category.get_absolute_url()},
            {'title': product.name, 'url': ''},
        ],
    })


def search(request):
    q = request.GET.get('q', '').strip()
    qs = Product.objects.active().with_category()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    breadcrumbs = [{'title': 'Головна', 'url': '/'}, {'title': f'Пошук: {q}', 'url': ''}]
    return _product_list_context(request, qs, f'Результати пошуку: {q}', breadcrumbs)


def search_suggest(request):
    q = request.GET.get('q', '').strip()
    products = []
    if len(q) >= 2:
        products = Product.objects.active().filter(
            Q(name__icontains=q) | Q(sku__icontains=q),
        )[:6]
    html = render_to_string('partials/search_suggest.html', {'products': products, 'q': q})
    return HttpResponse(html)


def sale_list(request):
    qs = Product.objects.active().with_category().on_sale()
    breadcrumbs = [{'title': 'Головна', 'url': '/'}, {'title': 'Акції', 'url': ''}]
    return _product_list_context(request, qs, 'Акції', breadcrumbs)


def compare_page(request):
    from src.cart.compare import CompareService
    svc = CompareService(request)
    products = svc.get_products()
    attr_names = []
    for p in products:
        for a in p.attributes.filter(show_in_compare=True):
            if a.name not in attr_names:
                attr_names.append(a.name)
    return render(request, 'catalog/compare.html', {
        'products': products,
        'attr_names': attr_names,
        'page_title': 'Порівняння товарів',
    })
