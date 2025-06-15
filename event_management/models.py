from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex

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
    #organizer = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='organized_events')
    organizer = models.ForeignKey('authentication.Organizer',  on_delete=models.CASCADE,related_name='events')
    is_featured = models.BooleanField(default=False)
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

class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']