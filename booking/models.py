# booking/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from event_management.models import Event, TicketType  # Added TicketType import
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import secrets
import string
import base64
from decimal import Decimal
from payments.platform_fees import calculate_platform_fee as calc_fee

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
        return sum(item.subtotal for item in self.items.all())
    
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
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)  # NEW: Added TicketType
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'booking_cart_item'
        unique_together = ['cart', 'ticket_type']  # Changed from event to ticket_type
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.quantity}x {self.ticket_type.name} for {self.event.title}"
    
    @property
    def subtotal(self):
        """Calculate the subtotal for this cart item"""
        return self.quantity * self.ticket_type.price
    
    @property
    def total_price(self):
        """Alias for subtotal for compatibility"""
        return self.subtotal


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
    qr_code = models.TextField(blank=True, null=True)
    
    # Billing information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    
    # Payment information
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # PayPal payment info
    paypal_order_id = models.CharField(max_length=255, blank=True)
    paypal_capture_id = models.CharField(max_length=255, blank=True)
    paypal_payer_id = models.CharField(max_length=255, blank=True)
    
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
            'confirmed': 'success',
            'cancelled': 'danger',
            'refunded': 'dark'
        }
        return colors.get(self.status, 'secondary')

    def calculate_platform_fee(self):
        """Calculate platform fee using environment-based tiers"""
        return calc_fee(self.total_amount)
    
    def organizer_payout(self):
        """Amount organizer receives after platform fee"""
        return self.total_amount - self.calculate_platform_fee()
    
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
    def generate_qr_code(self):
        """Generate QR code for this ticket that opens validation URL when scanned"""
        from django.urls import reverse
        from django.conf import settings

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=5,
        )

        # Generate the validation URL
        validation_path = reverse('booking:validate_ticket', kwargs={'ticket_code': self.ticket_number})

        # Create full URL - make sure this matches your actual domain
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        validation_url = f"{base_url}{validation_path}"

        # IMPORTANT: Add only the URL, not a dictionary
        qr.add_data(validation_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 string for TextField storage
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        self.qr_code = img_str
        self.save()

        return self.qr_code

class OrderItem(models.Model):
    """Individual ticket type booking in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='booking_orderitems')  # NEW: Added TicketType
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    
    class Meta:
        db_table = 'booking_order_item'
        unique_together = ['order', 'ticket_type']  # Changed from event to ticket_type
    
    def __str__(self):
        return f"{self.quantity}x {self.ticket_type.name} for {self.event.title}"
    
    @property
    def total_price(self):
        """Calculate total price for this order item"""
        return self.quantity * self.price

    # You can also remove the get_total method since it duplicates total_price
    def get_total(self):
        return self.quantity * self.price

    # Keep the subtotal property as an alias
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
        
        # Update quantity sold on ticket type
        self.ticket_type.quantity_sold += self.quantity
        self.ticket_type.save()
        
        return tickets
    
    def generate_ticket_number(self):
        """Generate unique ticket number"""
        return f"TKT{self.order.order_number}-{self.ticket_type.id}-{uuid.uuid4().hex[:8].upper()}"


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
    
    @property
    def ticket_type(self):
        """Get the ticket type from order item"""
        return self.order_item.ticket_type
    
    def generate_qr_code(self):
        """Generate QR code for this ticket that mobile devices can scan and open"""
        from django.urls import reverse
        from django.conf import settings
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=5,
        )
        
        # Generate the validation URL path
        validation_path = reverse('booking:validate_ticket', kwargs={'ticket_code': self.ticket_number})
        
        # Create full URL that mobile devices can open
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        validation_url = f"{base_url}{validation_path}"
        
        # CRITICAL: Add only the clean URL, not a dictionary or JSON
        qr.add_data(validation_url)
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


class Booking(models.Model):
    event = models.ForeignKey('event_management.Event', on_delete=models.CASCADE, related_name='booking_bookings')
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='booking_user_bookings')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    paypal_order_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class BookingTicket(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    ticket_type = models.ForeignKey('event_management.TicketType', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)