# authentication/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    """
    Custom User model for the Jersey Event Platform
    """
    # Additional fields for all users
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # User preferences
    newsletter_subscription = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Profile
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Metadata
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_organizer(self):
        """Check if user has an organizer profile"""
        return hasattr(self, 'organizer')


class Organizer(models.Model):
    """
    Organizer model for users who can create and manage events
    Uses PayPal for payment processing (Jersey-compatible)
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='organizer'
    )
    
    # Business Information
    company_name = models.CharField(max_length=255)
    company_registration = models.CharField(max_length=100, blank=True)
    vat_number = models.CharField(max_length=50, blank=True)
    
    # Contact Information
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    
    # Address
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    parish = models.CharField(
        max_length=50,
        choices=[
            ('St Helier', 'St Helier'),
            ('St Clement', 'St Clement'),
            ('St Saviour', 'St Saviour'),
            ('St Brelade', 'St Brelade'),
            ('St Lawrence', 'St Lawrence'),
            ('St Peter', 'St Peter'),
            ('St Mary', 'St Mary'),
            ('St John', 'St John'),
            ('St Ouen', 'St Ouen'),
            ('St Martin', 'St Martin'),
            ('Grouville', 'Grouville'),
            ('Trinity', 'Trinity'),
        ],
        default='St Helier'
    )
    postal_code = models.CharField(max_length=10)
    
    # PayPal Integration (Replacing Stripe)
    paypal_email = models.EmailField(
        blank=True,
        help_text="PayPal Business account email for receiving payments"
    )
    payment_ready = models.BooleanField(
        default=False,
        help_text="Whether PayPal account is set up and ready to receive payments"
    )
    payment_setup_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payment account was set up"
    )
    
    # Legacy Stripe fields - kept for migration purposes, will be removed later
    # stripe_account_id = models.CharField(max_length=255, blank=True)
    # stripe_onboarding_complete = models.BooleanField(default=False)
    # stripe_charges_enabled = models.BooleanField(default=False)
    # stripe_payouts_enabled = models.BooleanField(default=False)
    # stripe_details_submitted = models.BooleanField(default=False)
    # stripe_last_update = models.DateTimeField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(
        default=False,
        help_text="Verified by platform admin"
    )
    verification_documents = models.FileField(
        upload_to='organizer_docs/',
        blank=True,
        null=True
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_organizers'
    )
    
    # Financial Settings
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text="Platform commission percentage"
    )
    
    # Profile
    logo = models.ImageField(upload_to='organizer_logos/', blank=True, null=True)
    description = models.TextField(help_text="About your organization")
    
    # Social Media
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizers'
        verbose_name = 'Organizer'
        verbose_name_plural = 'Organizers'
        
    def __str__(self):
        return f"{self.company_name} ({self.user.email})"
    
    @property
    def can_create_events(self):
        """Check if organizer can create events"""
        return self.is_verified
    
    @property
    def can_receive_payments(self):
        """Check if organizer can receive payments through PayPal"""
        return all([
            self.is_verified,
            self.paypal_email,
            self.payment_ready
        ])
    
    @property
    def payment_setup_required(self):
        """Check if payment setup is needed"""
        return not self.paypal_email or not self.payment_ready
    
    @property
    def payment_status_display(self):
        """Human-readable payment status"""
        if not self.paypal_email:
            return "Not Started"
        elif not self.payment_ready:
            return "Incomplete"
        else:
            return "Active"
    
    @property
    def stripe_onboarding_complete(self):
        """Legacy property for backward compatibility - maps to payment_ready"""
        return self.payment_ready
    
    def get_platform_fee_amount(self, total_amount):
        """Calculate platform fee for a given amount"""
        return (total_amount * self.commission_rate) / 100
    
    def save(self, *args, **kwargs):
        # Auto-verify if user is staff/superuser
        if self.user.is_staff or self.user.is_superuser:
            self.is_verified = True
            if not self.verified_at:
                self.verified_at = timezone.now()
        
        # Set payment setup date when PayPal is configured
        if self.paypal_email and self.payment_ready and not self.payment_setup_date:
            self.payment_setup_date = timezone.now()
        
        super().save(*args, **kwargs)