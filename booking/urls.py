# booking/urls.py

from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<slug:event_slug>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Checkout URLs
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/process/', views.process_payment, name='process_payment'),
    path('checkout/success/<str:order_number>/', views.order_success, name='order_success'),
    
    # Order URLs
    path('orders/', views.order_history, name='order_history'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/tickets/', views.download_tickets, name='download_tickets'),
    
    # Webhook
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]