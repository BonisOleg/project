from .services import CartService


def cart_context(request):
    cart = CartService(request)
    from .compare import CompareService
    compare = CompareService(request)
    return {
        'cart_count': cart.count,
        'cart_subtotal': cart.subtotal,
        'compare_count': compare.count,
    }
