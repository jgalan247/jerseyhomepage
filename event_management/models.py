from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex
import urllib.parse
from datetime import timedelta
from urllib.parse import quote_plus
from decimal import Decimal
from .pricing import PricingService

# Don't call get_user_model() at module level
User = get_user_model()  # Remove this line

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class PublicEventManager(models.Manager):
    """Manager that returns only approved and active events for public view"""
    def get_queryset(self):
        return super().get_queryset().filter(
            is_approved=True,
            is_active=True,
            date__gte=timezone.now()  # Only future events
        )


class Event(models.Model):
    # Existing fields
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200) 
    description = models.TextField()
    venue = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='events')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    capacity = models.IntegerField(default=100)
    tickets_sold = models.IntegerField(default=0)
    organizer = models.ForeignKey('authentication.Organizer', on_delete=models.CASCADE, related_name='events')
    
    # Status flags
    is_featured = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False) 
    is_active = models.BooleanField(default=True)
    pet_friendly = models.BooleanField(default=False)
    family_friendly = models.BooleanField(default=True)
    has_offers = models.BooleanField(default=False)
    
        # Add these new fields
    platform_plan = models.ForeignKey('PlatformPlan', on_delete=models.PROTECT, null=True, blank=True)
    plan_paid = models.BooleanField(default=False)
    #listing_fee_paid = models.BooleanField(default=False)
    #listing_fee_amount = models.DecimalField(max_digits=6, decimal_places=2, default=25.00)
    paypal_order_id = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    listing_fee = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    default=Decimal('0'),
    help_text="Platform listing fee for this event"
    )
    listing_tier = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Pricing tier applied"
    )
    listing_paid = models.BooleanField(
        default=False,
        help_text="Has the listing fee been paid?"
    )
    listing_paid_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the listing fee was paid"
    )
    
    # Event approval (add these)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('pending_payment', 'Pending Payment'),
            ('pending_review', 'Pending Review'),
            ('approved', 'Approved'),
            ('published', 'Published'),
            ('rejected', 'Rejected'),
            ('completed', 'Completed'),
        ],
        default='draft',
        help_text="Event status in the system"
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Notes from admin (rejection reasons, etc.)"
    )
    reviewed_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_events',
        help_text="Admin who reviewed this event"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the event was reviewed"
    )
   
    # Approval fields
    is_approved = models.BooleanField(
        default=False,
        help_text="Event must be approved by admin before appearing publicly"
    )
    approved_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='approved_events'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True)
    
    # Managers
    objects = models.Manager()  # Default manager - returns all events
    public = PublicEventManager()  # Only approved events for public
    
    class Meta:
        ordering = ['date']
        indexes = [
            GinIndex(fields=['search_vector']),
        ]
        permissions = [
            ("can_approve_events", "Can approve events"),
        ]
    
    def __str__(self):
        return self.title
    
    def approve(self, user):
        """Approve the event"""
        self.is_approved = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self):
        """Reject/unapprove the event"""
        self.is_approved = False
        self.approved_by = None
        self.approved_at = None
        self.save()
    
    # Add this method to calculate pricing when saving
    def calculate_listing_fee(self):
        """Calculate the listing fee for this event"""
        from .pricing import PricingService
        
        # Pass ticket_price for percentage-based calculation
        fee, tier_name = PricingService.calculate_event_fee(
            capacity=self.capacity,
            is_free_event=(self.price == 0 or self.price is None),
            ticket_price=self.price  # Add ticket price for percentage calculation
        )
    
        self.listing_fee = fee
        self.listing_tier = tier_name
        return fee, tier_name
        
    @property
    def status_display(self):
        """Human-readable status"""
        if not self.is_active:
            return "Inactive"
        elif not self.is_approved:
            return "Pending Approval"
        elif self.has_passed:
            return "Past Event"
        elif self.is_sold_out:
            return "Sold Out"
        else:
            return "Active"
    
    @property
    def can_be_booked(self):
        """Check if event can accept bookings"""
        return (
            self.is_approved and 
            self.is_active and 
            not self.has_passed and 
            not self.is_sold_out
        )
    @property
    def total_tickets_configured(self):
        """Total tickets across all ticket types"""
        return self.ticket_types.aggregate(total=models.Sum('quantity_available'))['total'] or 0
    
    @property
    def total_tickets_sold(self):
        """Total tickets sold across all types"""
        return self.ticket_types.aggregate(total=models.Sum('quantity_sold'))['total'] or 0
    
    @property
    def is_published(self):
        """Event is only visible if plan is paid"""
        return self.plan_paid and self.status == 'approved'
    
    def get_absolute_url(self):
        return reverse('event_management:event_detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        # Generate slug if not present
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
            if not self.slug:  # If title doesn't produce a valid slug
                self.slug = f"event-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        super().save(*args, **kwargs)
        
        # Update search vector
        if self.pk:  # Only update if the object has been saved
            Event.objects.filter(pk=self.pk).update(
                search_vector=SearchVector('title', weight='A') + 
                            SearchVector('description', weight='B') +
                            SearchVector('venue', weight='C') +
                            SearchVector('address', weight='D')
            )
    
    @property
    def is_sold_out(self):
        return self.tickets_sold >= self.capacity
    
    @property
    def tickets_available(self):
        return self.capacity - self.tickets_sold
    
    @property
    def is_free(self):
        return self.price == 0
    
    @property
    def is_upcoming(self):
        return self.date > timezone.now()
    
    # Add these properties for the booking system
    @property
    def available_tickets(self):
        """Calculate available tickets"""
        if not self.capacity:
            return 999  # Unlimited
        return max(0, self.capacity - self.tickets_sold)
    
    @property
    def has_passed(self):
        """Check if event has already happened"""
        return self.date < timezone.now()
    
    @property
    def time(self):
        """Return just the time portion of the date"""
        return self.date.time()
    
    @property
    def location(self):
        """Alias for address - used in templates"""
        return self.address

    def get_google_maps_url(self):
        """Generate Google Maps URL for the venue"""
        
        query = f"{self.venue}, {self.address}"
        return f"https://maps.google.com/maps?q={urllib.parse.quote(query)}"

    def get_share_urls(self):
        """Generate social media share URLs"""
        # Get full URL for the event
        domain = "https://jersey.live"  # Update this with your actual domain
        event_url = f"{domain}{self.get_absolute_url()}"
        
        # Event details for sharing
        title = quote_plus(self.title)
        description = quote_plus(f"{self.title} - {self.date.strftime('%d %B %Y')} at {self.venue}")
        
        return {
            'facebook': f"https://www.facebook.com/sharer/sharer.php?u={quote_plus(event_url)}",
            'twitter': f"https://twitter.com/intent/tweet?text={title}&url={quote_plus(event_url)}",
            'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={quote_plus(event_url)}",
            'whatsapp': f"https://wa.me/?text={description}%20{quote_plus(event_url)}",
            'email': f"mailto:?subject={title}&body={description}%0A%0AMore%20info:%20{quote_plus(event_url)}"
        }
    
    def get_calendar_links(self):
            """Generate calendar links for the event"""
            # Event details
            title = urllib.parse.quote(self.title)
            details = urllib.parse.quote(self.description[:200] + "..." if len(self.description) > 200 else self.description)
            location = urllib.parse.quote(f"{self.venue}, {self.address}")
            
            # Format dates for Google Calendar (YYYYMMDDTHHmmSSZ format)
            start_date = self.date.strftime('%Y%m%dT%H%M%S')
            end_date = (self.end_date if self.end_date else self.date + timedelta(hours=2)).strftime('%Y%m%dT%H%M%S')
            
            # Google Calendar link
            google_url = (
                f"https://calendar.google.com/calendar/render?action=TEMPLATE"
                f"&text={title}"
                f"&dates={start_date}/{end_date}"
                f"&details={details}"
                f"&location={location}"
                f"&sf=true&output=xml"
            )
            
            # ICS download link (using your existing download_ics view)
            ics_url = f"/event/{self.slug}/download-ics/"
            
            return {
                'google': google_url,
                'ics': ics_url
            }

class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']

class PlatformPlan(models.Model):
    """Platform subscription plans for organizers"""
    PLAN_TYPE_CHOICES = [
        ('per_event', 'Per Event'),
        ('monthly', 'Monthly Subscription'),
        ('annual', 'Annual Subscription'),
    ]
    
    name = models.CharField(max_length=50)  # "Starter", "Growth", "Pro"
    slug = models.SlugField(unique=True)
    max_tickets = models.IntegerField(help_text="-1 for unlimited")
    
    # Pricing options
    price_per_event = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_month = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    price_per_year = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Features
    features = models.JSONField(default=dict)
    """
    Example features:
    {
        "analytics": "basic|advanced",
        "support": "email|priority",
        "custom_branding": true|false,
        "featured_listing": true|false,
        "email_attendees": true|false,
        "max_ticket_types": 3|10|unlimited
    }
    """
    
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', 'price_per_event']
    
    def __str__(self):
        return f"{self.name} - £{self.price_per_event}/event"


class TicketType(models.Model):
    """Different ticket tiers for an event"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=100)  # "Early Bird", "General", "VIP"
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Availability
    quantity_available = models.IntegerField()
    quantity_sold = models.IntegerField(default=0)
    
    # Sale window
    sale_starts = models.DateTimeField(default=timezone.now)
    sale_ends = models.DateTimeField()
    
    # Display
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['display_order', 'price']
    
    def __str__(self):
        return f"{self.event.title} - {self.name} (£{self.price})"
    
    @property
    def is_available(self):
        """Check if tickets can be purchased"""
        now = timezone.now()
        return (
            self.is_active and
            self.sale_starts <= now <= self.sale_ends and
            self.quantity_sold < self.quantity_available
        )
    
    @property
    def remaining_quantity(self):
        return self.quantity_available - self.quantity_sold


class EventPlanPayment(models.Model):
    """Track platform fee payments for events"""
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='plan_payment')
    plan = models.ForeignKey(PlatformPlan, on_delete=models.PROTECT)
    amount_paid = models.DecimalField(max_digits=6, decimal_places=2)
    paypal_order_id = models.CharField(max_length=255)
    paid_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event.title} - {self.plan.name} - £{self.amount_paid}"

# Add this to your existing event_management/models.py

class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Payment'
    CONFIRMED = 'confirmed', 'Confirmed'
    CANCELLED = 'cancelled', 'Cancelled'
    REFUNDED = 'refunded', 'Refunded'

class Booking(models.Model):
    # Existing fields...
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_user_bookings')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    
    # Link to payment
    order = models.ForeignKey('payments.Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Booking details
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    booking_reference = models.CharField(max_length=20, unique=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Contact info for guests
    attendee_name = models.CharField(max_length=255)
    attendee_email = models.EmailField()
    attendee_phone = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    @property
    def is_confirmed(self):
        return self.status == BookingStatus.CONFIRMED and self.order and self.order.status == 'completed'
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.event.title}"