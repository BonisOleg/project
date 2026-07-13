from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.db.models import Q

from .models import ProductAttribute


def _parse_decimal(value):
    if value in (None, ''):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _brand_slugs(params):
    values = params.getlist('brand') if hasattr(params, 'getlist') else [params.get('brand', '')]
    slugs = []
    for raw in values:
        if not raw:
            continue
        for part in str(raw).split(','):
            slug = part.strip()
            if slug and slug not in slugs:
                slugs.append(slug)
    return slugs


def attr_param_key(name):
    return f'attr_{name}'


class ProductFilter:
    def __init__(self, queryset, params):
        self.qs = queryset
        self.params = params

    def apply(self):
        qs = self.qs
        q = self.params.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))

        category_slug = self.params.get('category')
        if category_slug:
            from .models import Category
            try:
                cat = Category.objects.get(slug=category_slug, is_active=True)
                ids = cat.get_descendant_ids()
                qs = qs.filter(category_id__in=ids)
            except Category.DoesNotExist:
                pass

        brands = _brand_slugs(self.params)
        if brands:
            qs = qs.filter(brand__slug__in=brands)

        price_min = _parse_decimal(self.params.get('price_min'))
        price_max = _parse_decimal(self.params.get('price_max'))
        if price_min is not None:
            qs = qs.filter(price__gte=price_min)
        if price_max is not None:
            qs = qs.filter(price__lte=price_max)

        if self.params.get('in_stock'):
            qs = qs.filter(availability='in_stock')

        if self.params.get('sale'):
            qs = qs.filter(is_on_sale=True)

        for key in self.params.keys():
            if not key.startswith('attr_'):
                continue
            name = key[5:]
            if not name:
                continue
            values = self.params.getlist(key) if hasattr(self.params, 'getlist') else [self.params.get(key)]
            values = [v.strip() for v in values if v and str(v).strip()]
            if not values:
                continue
            qs = qs.filter(attributes__name=name, attributes__value__in=values)

        sort = self.params.get('sort', 'popular')
        sort_map = {
            'popular': ('-sort_order', '-views_count'),
            'price_asc': ('price',),
            'price_desc': ('-price',),
            'name': ('name',),
            'new': ('-created_at',),
        }
        return qs.distinct().order_by(*sort_map.get(sort, sort_map['popular']))


def build_attr_facets(queryset, limit_names=12, limit_values=20):
    rows = (
        ProductAttribute.objects
        .filter(product_id__in=queryset.values('pk'))
        .values_list('name', 'value')
        .distinct()
        .order_by('name', 'value')
    )
    grouped = defaultdict(list)
    for name, value in rows:
        if not name or not value:
            continue
        if name not in grouped and len(grouped) >= limit_names:
            continue
        bucket = grouped[name]
        if value not in bucket and len(bucket) < limit_values:
            bucket.append(value)
    return [
        {'name': name, 'param': attr_param_key(name), 'values': values}
        for name, values in grouped.items()
        if values
    ]


def mark_attr_facets(facets, selected_attrs):
    marked = []
    for facet in facets:
        selected = selected_attrs.get(facet['name'], set())
        marked.append({
            'name': facet['name'],
            'param': facet['param'],
            'values': [
                {'value': value, 'selected': value in selected}
                for value in facet['values']
            ],
        })
    return marked


PER_PAGE_CHOICES = (12, 24, 48)
DEFAULT_PER_PAGE = 12


def resolve_per_page(params):
    try:
        value = int(params.get('per_page', DEFAULT_PER_PAGE))
    except (TypeError, ValueError):
        return DEFAULT_PER_PAGE
    return value if value in PER_PAGE_CHOICES else DEFAULT_PER_PAGE
