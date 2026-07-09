from .services import WishlistService


def wishlist_context(request):
    wishlist = WishlistService(request)
    return {
        'wishlist_count': wishlist.count,
        'wishlist_product_ids': wishlist.product_ids(),
    }
