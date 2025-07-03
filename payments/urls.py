from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path('paypal/setup/', views.paypal_setup, name='paypal_setup'),
    # Only the URLs that have working views
    path("tickets/<int:event_id>/", views.TicketPurchaseView.as_view(), name="ticket_purchase"),
    path("listing-fee/<int:event_id>/", views.ListingFeeView.as_view(), name="listing_fee"),
    path("success/<int:order_id>/", views.PaymentSuccessView.as_view(), name="payment_success"),
    path("cancel/<int:order_id>/", views.PaymentCancelView.as_view(), name="payment_cancel"),
]
