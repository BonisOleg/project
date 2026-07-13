from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from src.core.breadcrumbs import make_breadcrumbs

from .filters import (
    PER_PAGE_CHOICES,
    ProductFilter,
    build_attr_facets,
    mark_attr_facets,
    resolve_per_page,
)
from .models import Brand, Category, Product


def _query_without_page(params):
    qd = params.copy()
    qd.pop('page', None)
    return qd.urlencode()


def _selected_brands(params):
    if hasattr(params, 'getlist'):
        values = params.getlist('brand')
    else:
        values = [params.get('brand', '')]
    selected = set()
    for raw in values:
        if not raw:
            continue
        for part in str(raw).split(','):
            slug = part.strip()
            if slug:
                selected.add(slug)
    return selected


def _selected_attrs(params):
    selected = {}
    for key in params.keys():
        if not key.startswith('attr_'):
            continue
        name = key[5:]
        if not name:
            continue
        values = params.getlist(key) if hasattr(params, 'getlist') else [params.get(key)]
        selected[name] = {v for v in values if v}
    return selected


def _product_list_context(request, base_qs, page_title, breadcrumbs, category=None, show_types=False):
    annotated = base_qs.annotate_rating()
    selected_attrs = _selected_attrs(request.GET)
    attr_facets = mark_attr_facets(build_attr_facets(annotated), selected_attrs)
    filtered = ProductFilter(annotated, request.GET).apply()
    per_page = resolve_per_page(request.GET)
    paginator = Paginator(filtered, per_page)
    page = paginator.get_page(request.GET.get('page'))
    sort = request.GET.get('sort', 'popular') or 'popular'
    query_wo_page = _query_without_page(request.GET)
    context = {
        'products': page,
        'page_obj': page,
        'page_title': page_title,
        'breadcrumbs': breadcrumbs,
        'category': category,
        'brands': Brand.objects.filter(is_active=True),
        'root_categories': Category.objects.filter(parent=None, is_active=True).prefetch_related('children'),
        'attr_facets': attr_facets,
        'selected_brands': _selected_brands(request.GET),
        'selected_category': request.GET.get('category', ''),
        'current_sort': sort,
        'per_page': per_page,
        'per_page_choices': PER_PAGE_CHOICES,
        'result_count': paginator.count,
        'show_types': show_types,
        'query_string': query_wo_page,
    }
    if request.htmx:
        return render(request, 'catalog/_product_grid.html', context)
    return render(request, 'catalog/list.html', context)


def catalog_list(request):
    qs = Product.objects.active().with_category()
    breadcrumbs = make_breadcrumbs(('Каталог', ''))
    return _product_list_context(
        request, qs, 'Усі товари', breadcrumbs, show_types=True,
    )


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    ids = category.get_descendant_ids()
    qs = Product.objects.active().with_category().filter(category_id__in=ids)
    parts = [('Каталог', '/catalog/')]
    if category.parent:
        parts.append((category.parent.name, category.parent.get_absolute_url()))
    parts.append((category.name, ''))
    return _product_list_context(
        request, qs, category.meta_title or category.name, make_breadcrumbs(*parts), category,
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.active().with_category().annotate_rating(), slug=slug,
    )
    product.increment_views()
    similar = Product.objects.active().filter(
        category=product.category,
    ).exclude(pk=product.pk)[:12]
    parts = [('Каталог', '/catalog/')]
    category = product.category
    if category.parent:
        parts.append((category.parent.name, category.parent.get_absolute_url()))
    parts.append((category.name, category.get_absolute_url()))
    parts.append((product.name, ''))
    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'similar_products': similar,
        'breadcrumbs': make_breadcrumbs(*parts),
    })


def search(request):
    q = request.GET.get('q', '').strip()
    qs = Product.objects.active().with_category()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    label = f'Пошук: {q}' if q else 'Пошук'
    breadcrumbs = make_breadcrumbs(('Каталог', '/catalog/'), (label, ''))
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
    breadcrumbs = make_breadcrumbs(('Каталог', '/catalog/'), ('Акції', ''))
    return _product_list_context(request, qs, 'Акції', breadcrumbs)


def compare_page(request):
    from src.cart.compare import CompareService
    svc = CompareService(request)
    products = svc.get_products()
    attr_names = []
    for p in products:
        for a in p.attributes.all():
            if a.show_in_compare and a.name not in attr_names:
                attr_names.append(a.name)
    return render(request, 'catalog/compare.html', {
        'products': products,
        'attr_names': attr_names,
        'page_title': 'Порівняння товарів',
        'breadcrumbs': make_breadcrumbs(('Каталог', '/catalog/'), ('Порівняння', '')),
    })
