# booking/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem, Order, OrderItem, Ticket, GuestCheckout


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'total_items', 'total_price', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['session_key']
    readonly_fields = ['session_key', 'total_items', 'total_price']
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Total Items'
    
    def total_price(self, obj):
        return f'£{obj.total_price:.2f}'
    total_price.short_description = 'Total Price'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['event', 'ticket_type', 'quantity', 'total_price']
    
    def total_price(self, obj):
        return f'£{obj.total_price:.2f}'
    total_price.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    # ✅ Fixed to use actual fields: added_at (not created_at), ticket_type
    list_display = ['cart', 'event', 'ticket_type', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at']  # ✅ Changed from created_at to added_at
    search_fields = ['event__title', 'ticket_type__name', 'cart__session_key']
    
    def total_price(self, obj):
        return f'£{obj.total_price:.2f}'
    total_price.short_description = 'Total'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['event', 'ticket_type', 'quantity', 'price', 'total_price']
    
    def total_price(self, obj):
        return f'£{obj.total_price:.2f}'
    total_price.short_description = 'Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'email', 'customer_name', 'total_amount', 'status', 'created_at', 'is_paid']
    list_filter = ['status', 'created_at', 'paid_at']
    search_fields = ['order_number', 'email', 'first_name', 'last_name', 'paypal_order_id']
    readonly_fields = ['order_number', 'paypal_order_id', 'paypal_capture_id', 'paypal_payer_id', 'ip_address', 'created_at', 'updated_at', 'paid_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status', 'total_amount', 'created_at', 'updated_at', 'paid_at')
        }),
        ('Customer Information', {
            'fields': ('user', 'email', 'first_name', 'last_name', 'phone')
        }),
        ('Payment Information', {
            'fields': ('paypal_order_id', 'paypal_capture_id', 'paypal_payer_id')
        }),
        ('Additional Information', {
            'fields': ('notes', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_name(self, obj):
        return obj.customer_name
    customer_name.short_description = 'Customer Name'
    
    def is_paid(self, obj):
        return obj.is_paid
    is_paid.boolean = True
    is_paid.short_description = 'Paid'
    
    actions = ['mark_as_paid', 'export_orders']
    
    def mark_as_paid(self, request, queryset):
        for order in queryset:
            order.mark_as_paid()
        self.message_user(request, f'{queryset.count()} orders marked as paid.')
    mark_as_paid.short_description = 'Mark selected orders as paid'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'event', 'ticket_type', 'quantity', 'price', 'total_price']
    list_filter = ['order__created_at', 'event', 'ticket_type']
    search_fields = ['order__order_number', 'event__title', 'ticket_type__name']
    
    def total_price(self, obj):
        return f'£{obj.total_price:.2f}'
    total_price.short_description = 'Total'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'event_display', 'ticket_type_display', 'order_display', 'is_used', 'used_at', 'qr_code_preview']
    list_filter = ['is_used', 'order_item__event', 'order_item__ticket_type', 'order_item__order__created_at']
    search_fields = ['ticket_number', 'order_item__order__order_number', 'order_item__event__title']
    readonly_fields = ['ticket_number', 'qr_code_preview_large', 'order_item', 'is_used', 'used_at']
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_number', 'order_item', 'qr_code_preview_large')
        }),
        ('Usage Information', {
            'fields': ('is_used', 'used_at')
        }),
    )
    
    def event_display(self, obj):
        return obj.event.title
    event_display.short_description = 'Event'
    
    def ticket_type_display(self, obj):
        return obj.ticket_type.name
    ticket_type_display.short_description = 'Ticket Type'
    
    def order_display(self, obj):
        return obj.order.order_number
    order_display.short_description = 'Order'
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="data:image/png;base64,{}" width="50" height="50" />', obj.qr_code)
        return '-'
    qr_code_preview.short_description = 'QR Code'
    
    def qr_code_preview_large(self, obj):
        if obj.qr_code:
            return format_html('<img src="data:image/png;base64,{}" width="200" height="200" />', obj.qr_code)
        return 'No QR code generated'
    qr_code_preview_large.short_description = 'QR Code'
    
    actions = ['mark_as_used', 'mark_as_unused', 'regenerate_qr_codes']
    
    def mark_as_used(self, request, queryset):
        for ticket in queryset:
            ticket.mark_as_used()
        self.message_user(request, f'{queryset.count()} tickets marked as used.')
    mark_as_used.short_description = 'Mark selected tickets as used'
    
    def mark_as_unused(self, request, queryset):
        queryset.update(is_used=False, used_at=None)
        self.message_user(request, f'{queryset.count()} tickets marked as unused.')
    mark_as_unused.short_description = 'Mark selected tickets as unused'
    
    def regenerate_qr_codes(self, request, queryset):
        for ticket in queryset:
            ticket.generate_qr_code()
        self.message_user(request, f'QR codes regenerated for {queryset.count()} tickets.')
    regenerate_qr_codes.short_description = 'Regenerate QR codes'


@admin.register(GuestCheckout)
class GuestCheckoutAdmin(admin.ModelAdmin):
    list_display = ['email', 'order', 'created_account', 'created_at']
    list_filter = ['created_account', 'created_at']
    search_fields = ['email', 'order__order_number']