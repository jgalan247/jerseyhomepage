from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Email is used as the primary authentication method.
    """
    email = models.EmailField(_('email address'), unique=True)
    is_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Additional profile fields
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Preferences
    newsletter_subscription = models.BooleanField(default=True)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email
    
    def regenerate_verification_token(self):
        """Generate a new email verification token."""
        self.email_verification_token = uuid.uuid4()
        self.save(update_fields=['email_verification_token'])
        return self.email_verification_token