from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter

from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'product_sku', 'price', 'quantity', 'line_total')
    can_delete = False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('order_number', 'email', 'phone', 'total', 'status', 'created_at')
    list_filter = [
        ('status', ChoicesDropdownFilter),
        ('delivery_service', ChoicesDropdownFilter),
    ]
    list_filter_submit = True
    search_fields = ('order_number', 'email', 'phone', 'first_name', 'last_name', 'tracking_number')
    readonly_fields = (
        'order_number', 'idempotency_key', 'liqpay_order_id', 'liqpay_transaction_id',
        'subtotal', 'discount', 'delivery_cost', 'total', 'created_at', 'updated_at',
    )
    autocomplete_fields = ('user',)
    inlines = [OrderItemInline]
    fieldsets = (
        ('Замовлення', {'fields': ('order_number', 'status', 'user', 'promo_code', 'comment')}),
        ('Клієнт', {'fields': ('first_name', 'last_name', 'phone', 'email', 'create_account')}),
        ('Доставка', {
            'fields': (
                'delivery_service', 'delivery_city', 'delivery_type',
                'delivery_address', 'tracking_number',
            ),
        }),
        ('Суми', {'fields': ('subtotal', 'discount', 'delivery_cost', 'total')}),
        ('Оплата', {
            'fields': ('liqpay_order_id', 'liqpay_transaction_id', 'idempotency_key'),
            'classes': ('collapse',),
        }),
        ('Службове', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
