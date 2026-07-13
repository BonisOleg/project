from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.db.models import Q

from .filter_schema import BONRO_ATTR_FACETS, BONRO_ATTR_FALLBACKS
from .models import CatalogFilter, ProductAttribute


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


def _attr_values_map(queryset, names, limit_values=30):
    if not names:
        return {}
    rows = (
        ProductAttribute.objects
        .filter(product_id__in=queryset.values('pk'), name__in=names)
        .values_list('name', 'value')
        .distinct()
        .order_by('name', 'value')
    )
    grouped = defaultdict(list)
    for name, value in rows:
        if not name or not value:
            continue
        bucket = grouped[name]
        if value not in bucket and len(bucket) < limit_values:
            bucket.append(value)
    return grouped


def get_active_catalog_filters():
    qs = CatalogFilter.objects.filter(is_active=True).order_by('sort_order', 'name')
    if qs.exists():
        return list(qs)
    # Fallback на хардкод Bonro, якщо в БД ще немає записів
    filters = []
    filters.append(CatalogFilter(
        name='Бренд', filter_type=CatalogFilter.TYPE_BRAND, sort_order=10, is_active=True,
    ))
    filters.append(CatalogFilter(
        name='Ціна, грн', filter_type=CatalogFilter.TYPE_PRICE, sort_order=20,
        is_active=True, open_by_default=True,
    ))
    filters.append(CatalogFilter(
        name='Вид', filter_type=CatalogFilter.TYPE_CATEGORY, sort_order=30, is_active=True,
    ))
    for i, name in enumerate(BONRO_ATTR_FACETS, start=1):
        fallback = '\n'.join(BONRO_ATTR_FALLBACKS.get(name, []))
        filters.append(CatalogFilter(
            name=name,
            filter_type=CatalogFilter.TYPE_ATTRIBUTE,
            attribute_name=name,
            fallback_values=fallback,
            sort_order=30 + i * 10,
            is_active=True,
        ))
    filters.append(CatalogFilter(
        name='Наявність', filter_type=CatalogFilter.TYPE_IN_STOCK, sort_order=200, is_active=True,
    ))
    return filters


def build_filter_sections(queryset, selected_attrs, limit_values=30):
    """Секції drawer-фільтра з адмінки (або fallback)."""
    definitions = get_active_catalog_filters()
    attr_names = [
        f.attribute_name or f.name
        for f in definitions
        if f.filter_type == CatalogFilter.TYPE_ATTRIBUTE and (f.attribute_name or f.name)
    ]
    values_map = _attr_values_map(queryset, attr_names, limit_values)

    sections = []
    for filt in definitions:
        section = {
            'id': filt.pk or f'fallback-{filt.filter_type}-{filt.name}',
            'name': filt.name,
            'filter_type': filt.filter_type,
            'open': bool(filt.open_by_default),
        }
        if filt.filter_type == CatalogFilter.TYPE_ATTRIBUTE:
            attr_name = filt.attribute_name or filt.name
            values = list(values_map.get(attr_name) or [])
            fallback = filt.fallback_list()
            if not values:
                values = fallback
            else:
                for extra in fallback:
                    if extra not in values and len(values) < limit_values:
                        values.append(extra)
            selected = selected_attrs.get(attr_name, set())
            section.update({
                'attr_name': attr_name,
                'param': attr_param_key(attr_name),
                'values': [
                    {'value': value, 'selected': value in selected}
                    for value in values
                ],
            })
        sections.append(section)
    return sections


# Зворотна сумісність для старих імпортів
def build_attr_facets(queryset, limit_values=30):
    sections = build_filter_sections(queryset, {}, limit_values)
    return [
        {
            'name': s['attr_name'],
            'param': s['param'],
            'values': [v['value'] for v in s['values']],
        }
        for s in sections
        if s['filter_type'] == CatalogFilter.TYPE_ATTRIBUTE
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
