# payments/models.py
from django.db import models
from django.contrib.auth import get_user_model
from event_management.models import Event, TicketType
from booking.models import Order
# import uuid

User = get_user_model()

class PaymentType(models.TextChoices):
    TICKET_PURCHASE = 'ticket_purchase', 'Ticket Purchase'
    LISTING_FEE = 'listing_fee', 'Listing Fee'

class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'
    CANCELLED = 'cancelled', 'Cancelled'

class PaymentAttempt(models.Model):
    """Track payment attempts for debugging and analytics"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='attempts')
    paypal_order_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']