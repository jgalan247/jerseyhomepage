# booking/urls.py
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('quick-add/', views.quick_add_to_cart, name='quick_add_to_cart'),
    
    # Checkout URLs
    path('checkout/', views.checkout_view, name='checkout'),
    
    # PayPal API endpoints (replacing Stripe)
    path('api/create-order/', views.create_ticket_order, name='create_ticket_order'),
    path('api/capture-payment/', views.capture_ticket_payment, name='capture_ticket_payment'),
    
    # Order URLs - FIXED duplicates
    path('order/<int:order_id>/success/', views.order_success, name='order_success'),
    path('order/<str:order_number>/tickets/', views.download_tickets, name='download_tickets'),
    path('ticket/<int:ticket_id>/download/', views.download_single_ticket, name='download_single_ticket'),
    
    # User order history
    path('orders/', views.order_history, name='order_history'),
    
    # PayPal webhook (if you implement it later)
    # path('paypal/webhook/', views.paypal_webhook, name='paypal_webhook'),
]