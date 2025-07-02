# payments/models.py
from django.db import models
from django.contrib.auth import get_user_model
from event_management.models import Event, TicketType
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

class Order(models.Model):
    # id field will be auto-created as integer
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    
    # Payment identifiers
    paypal_order_id = models.CharField(max_length=255, unique=True, blank=True)
    paypal_capture_id = models.CharField(max_length=255, blank=True)
    
    # Payment details
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Metadata
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For listing fees
    listing_duration_days = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.id} - {self.get_payment_type_display()} - {self.status}"
    
    @property
    def is_ticket_purchase(self):
        return self.payment_type == PaymentType.TICKET_PURCHASE
    
    @property
    def is_listing_fee(self):
        return self.payment_type == PaymentType.LISTING_FEE

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, null=True, blank=True, related_name='payment_orderitems')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.description} x{self.quantity}"
    
    @property
    def total_price(self):
        return self.price * self.quantity

class PaymentAttempt(models.Model):
    """Track payment attempts for debugging and analytics"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='attempts')
    paypal_order_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']