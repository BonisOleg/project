from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from src.core.breadcrumbs import make_breadcrumbs

from .models import Post


def post_list(request):
    posts = Post.objects.published()
    paginator = Paginator(posts, 9)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/list.html', {
        'page_obj': page,
        'page_title': 'Новини',
        'breadcrumbs': make_breadcrumbs(('Новини', '')),
    })


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.published(), slug=slug)
    return render(request, 'blog/detail.html', {
        'post': post,
        'breadcrumbs': make_breadcrumbs(
            ('Новини', '/blog/'),
            (post.title, ''),
        ),
    })
