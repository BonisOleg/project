from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from src.core.admin_filters import DropdownFiltersMixin, UkBooleanDropdownFilter

from .models import DeliveryAddress, User, WishlistItem


@admin.register(User)
class UserAdmin(DropdownFiltersMixin, DjangoUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('email', 'first_name', 'last_name', 'phone', 'bonus_points', 'is_staff', 'is_active')
    list_filter = [
        ('is_active', UkBooleanDropdownFilter),
        ('is_staff', UkBooleanDropdownFilter),
        ('is_superuser', UkBooleanDropdownFilter),
    ]
    ordering = ('email',)
    search_fields = ('email', 'phone', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональні', {'fields': ('first_name', 'last_name', 'phone', 'bonus_points')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Дати', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),
    )
    filter_horizontal = ('groups', 'user_permissions')


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(DropdownFiltersMixin, ModelAdmin):
    list_display = ('user', 'label', 'city', 'address', 'is_default')
    list_filter = [
        ('is_default', UkBooleanDropdownFilter),
    ]
    search_fields = ('user__email', 'city', 'address', 'label')
    autocomplete_fields = ('user',)


@admin.register(WishlistItem)
class WishlistItemAdmin(ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__email', 'product__name', 'product__sku')
    autocomplete_fields = ('user', 'product')
