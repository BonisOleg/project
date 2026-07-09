from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from src.catalog.models import Product

from .forms import AddressForm, LoginForm, PasswordResetForm, ProfileForm, RegisterForm
from .models import DeliveryAddress
from .services import WishlistService


class OyraLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        WishlistService(self.request).merge_session_to_user()
        return response


class OyraLogoutView(LogoutView):
    next_page = 'core:home'


class OyraPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    form_class = PasswordResetForm
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:cabinet')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if not form.cleaned_data.get('agree'):
            messages.error(request, 'Потрібна згода з договором')
        else:
            user = form.save()
            login(request, user)
            WishlistService(request).merge_session_to_user()
            messages.success(request, 'Реєстрація успішна')
            return redirect('accounts:cabinet')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def cabinet(request):
    return render(request, 'accounts/cabinet.html', {
        'orders': request.user.orders.all()[:10],
        'cabinet_section': 'orders',
    })


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Профіль оновлено')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {
        'form': form,
        'cabinet_section': 'profile',
    })


@require_POST
def wishlist_add(request, product_id):
    get_object_or_404(Product, pk=product_id, is_active=True)
    WishlistService(request).toggle(product_id)
    messages.success(request, 'Додано в обране')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    wished = WishlistService(request).toggle(product_id)
    variant = request.POST.get('variant', 'card')
    svc = WishlistService(request)

    if request.htmx:
        if not wished and request.POST.get('list_mode'):
            return HttpResponse(render_to_string('partials/wishlist_count.html', {
                'wishlist_count': svc.count,
            }, request=request))

        btn_html = render_to_string('partials/wishlist_btn.html', {
            'product': product,
            'wished': wished,
            'variant': variant,
        }, request=request)
        count_html = render_to_string('partials/wishlist_count.html', {
            'wishlist_count': svc.count,
        }, request=request)
        return HttpResponse(btn_html + count_html)

    messages.success(request, 'Додано в обране' if wished else 'Видалено з обраного')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def wishlist_remove(request, product_id):
    WishlistService(request).remove(product_id)
    if request.htmx:
        return HttpResponse(render_to_string('partials/wishlist_count.html', {
            'wishlist_count': WishlistService(request).count,
        }, request=request))
    return redirect('accounts:wishlist')


def wishlist_page(request):
    products = WishlistService(request).get_products()
    if request.user.is_authenticated:
        return render(request, 'accounts/wishlist.html', {
            'products': products,
            'cabinet_section': 'wishlist',
        })
    return render(request, 'accounts/wishlist_guest.html', {
        'products': products,
    })
