from decimal import Decimal

from django.db.models import Q


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

        brand = self.params.get('brand')
        if brand:
            qs = qs.filter(brand__slug=brand)

        price_min = self.params.get('price_min')
        price_max = self.params.get('price_max')
        if price_min:
            qs = qs.filter(price__gte=Decimal(price_min))
        if price_max:
            qs = qs.filter(price__lte=Decimal(price_max))

        if self.params.get('in_stock'):
            qs = qs.filter(availability='in_stock')

        if self.params.get('sale'):
            qs = qs.filter(is_on_sale=True)

        sort = self.params.get('sort', 'popular')
        sort_map = {
            'popular': ('-sort_order', '-views_count'),
            'price_asc': ('price',),
            'price_desc': ('-price',),
            'name': ('name',),
            'new': ('-created_at',),
        }
        return qs.order_by(*sort_map.get(sort, sort_map['popular']))
