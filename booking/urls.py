# booking/urls.py

from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),  # POST only, no slug needed
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),  # POST only
    
    path('test-stripe/', views.test_stripe, name='test_stripe'),
    # Checkout URLs
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/process/', views.process_payment, name='process_payment'),
    
    # Order URLs
    path('order/success/<str:order_number>/', views.order_success, name='order_success'),
    path('order/<str:order_number>/tickets/', views.download_tickets, name='download_tickets'),
    
    # User order history (comment out until implemented)
    # path('orders/', views.order_history, name='order_history'),
    # path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    
    # Webhook
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('order/<str:order_number>/tickets/', views.download_tickets, name='download_tickets'),
    path('ticket/<int:ticket_id>/download/', views.download_single_ticket, name='download_single_ticket'),  # Add this line
   
]