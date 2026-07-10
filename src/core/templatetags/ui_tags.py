from django import template

register = template.Library()


def ideal_cols(count, max_cols=4):
    n = max(1, count)
    if n <= max_cols:
        return n
    for c in range(max_cols, 1, -1):
        if n % c == 0:
            return c
    return max_cols


def pick_grid_columns(count: int) -> int:
    """Desktop: лише 5, 4 або 3 (product_grid_skill)."""
    if count <= 0:
        return 2
    if count <= 2:
        return 3

    for cols in (5, 4, 3):
        if count % cols == 0:
            return cols

    for cols in (4, 5, 3):
        if count % cols >= 3:
            return cols

    for cols in (3, 5, 4):
        if count % cols == 2:
            return cols

    return 3


@register.simple_tag
def product_grid_cols(count):
    return ideal_cols(count, 4)


@register.inclusion_tag('partials/product_grid_balanced.html')
def product_grid_balanced(products=None, list_mode=False):
    items = list(products) if products is not None else []
    return {
        'products': items,
        'grid_cols': pick_grid_columns(len(items)),
        'list_mode': list_mode,
    }


@register.simple_tag(takes_context=True)
def product_wished(context, product, wished=None):
    if wished not in (None, ''):
        return bool(wished)
    ids = context.get('wishlist_product_ids') or set()
    return product.pk in ids


@register.filter
def format_price(value):
    if value is None:
        return ''
    return f'{value:,.2f}'.replace(',', ' ').replace('.', ',') + ' грн'


CATEGORY_ACCENTS = {
    'sport': 'green',
    'dytiachi': 'yellow',
    'krisla': 'blue',
    'valizy': 'orange',
    'dim-i-sad': 'green',
    'budivnytstvo': 'blue',
    'traktory': 'green',
    'zootovary': 'yellow',
    'utsineni': 'raspberry',
    'sto': 'blue',
}


@register.filter
def category_accent(slug):
    return CATEGORY_ACCENTS.get(slug, 'blue')
