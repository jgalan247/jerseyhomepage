# booking/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from event_management.models import Event
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import secrets
import string
import base64

User = get_user_model()


class Cart(models.Model):
    """Session-based shopping cart"""
    session_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'booking_cart'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Cart {self.session_key}"
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """Individual items in a cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_cart_item'
        unique_together = ['cart', 'event']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.quantity}x {self.event.title}"
    
    @property
    def total_price(self):
        return self.quantity * self.price_at_time
    
    @property
    def subtotal(self):
        """Calculate the subtotal for this cart item"""
        return self.quantity * self.price
    
    # Alternative if price comes from event
    @property
    def subtotal(self):
        """Calculate the subtotal for this cart item"""
        return self.quantity * self.event.price

    def save(self, *args, **kwargs):
        if not self.price_at_time:
            self.price_at_time = self.event.price
        super().save(*args, **kwargs)


class Order(models.Model):
    """Order containing purchased tickets"""
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('processing', 'Processing'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    email = models.EmailField()  # For guest checkouts
    stripe_session_id = models.CharField(max_length=255, blank=True)
    qr_code = models.TextField(blank=True, null=True)
    # Billing information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    
    # Payment information
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Stripe payment info
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    stripe_checkout_session = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'booking_order'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_string = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return f"JER{timestamp}{random_string}"
    
    @property
    def is_paid(self):
        return self.status == 'confirmed' and self.paid_at is not None
    
    def get_status_color(self):
        """Return Bootstrap color class for status"""
        colors = {
            'pending': 'warning',
            'processing': 'info',
            'completed': 'success',
            'failed': 'danger',
            'cancelled': 'secondary',
            'refunded': 'dark'
        }
        return colors.get(self.status, 'secondary')

    def mark_as_paid(self):
        """Mark order as paid and generate tickets"""
        self.status = 'confirmed'
        self.paid_at = timezone.now()
        self.save()
        
        # Generate tickets for all order items
        for item in self.items.all():
            item.generate_tickets()

    @property
    def customer_email(self):
        """Alias for email - used in templates and utils"""
        return self.email
    
    @property
    def customer_name(self):
        """Full name of customer"""
        return f"{self.first_name} {self.last_name}".strip()

    def generate_qr_code(self):
        """Generate QR code for the entire order"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=5,
        )
        
        # Data to encode
        qr_data = {
            'order_number': self.order_number,
            'total_amount': str(self.total_amount),
            'created_at': self.created_at.isoformat(),
            'email': self.email,
        }
        
        qr.add_data(str(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        self.qr_code = img_str
        self.save()
        
        return self.qr_code


class OrderItem(models.Model):
    """Individual event booking in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'booking_order_item'
        unique_together = ['order', 'event']
    
    def __str__(self):
        return f"{self.quantity}x {self.event.title}"
    
    @property
    def total_price(self):
        return self.quantity * self.price
    
    @property
    def subtotal(self):
        return self.quantity * self.price
    
    def generate_tickets(self):
        """Generate tickets for this order item"""
        tickets = []
        for i in range(self.quantity):
            ticket = Ticket.objects.create(
                order_item=self,
                ticket_number=self.generate_ticket_number()
            )
            ticket.generate_qr_code()
            tickets.append(ticket)
        return tickets
    
    def generate_ticket_number(self):
        """Generate unique ticket number"""
        return f"TKT{self.order.order_number}-{uuid.uuid4().hex[:8].upper()}"


class Ticket(models.Model):
    """Individual ticket with QR code"""
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='tickets')
    ticket_number = models.CharField(max_length=64, unique=True)
    qr_code = models.TextField(blank=True, null=True) 
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'booking_ticket'
        ordering = ['ticket_number']
    
    def __str__(self):
        return self.ticket_number
    
    @property
    def event(self):
        return self.order_item.event
    
    @property
    def order(self):
        return self.order_item.order
    
    def generate_qr_code(self):
    
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=5,
        )
        
        # Data to encode in QR code
        qr_data = {
            'ticket_number': self.ticket_number,
            'event_id': self.event.id,
            'event_title': self.event.title,
            'event_date': self.event.date.isoformat(),
            'order_number': self.order.order_number,
        }
        
        qr.add_data(str(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string for TextField storage
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        self.qr_code = img_str
        self.save()
        
        return self.qr_code
        
    def mark_as_used(self):
        """Mark ticket as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()


class GuestCheckout(models.Model):
    """Store guest checkout information for conversion tracking"""
    email = models.EmailField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='guest_checkout')
    created_account = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_guest_checkout'