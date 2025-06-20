from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex
import urllib.parse
from datetime import timedelta
from urllib.parse import quote_plus

# Don't call get_user_model() at module level
# User = get_user_model()  # Remove this line

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

class Event(models.Model):
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
    is_featured = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False) 
    is_active = models.BooleanField(default=True)
    pet_friendly = models.BooleanField(default=False)
    family_friendly = models.BooleanField(default=True)
    has_offers = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True)
    
    class Meta:
        ordering = ['date']
        indexes = [
            GinIndex(fields=['search_vector']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('event_management:event_detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        """Override save to update search vector"""
        super().save(*args, **kwargs)
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

