from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.db import models

User = get_user_model()

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
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    pet_friendly = models.BooleanField(default=False)
    family_friendly = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})
    
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

class EventImage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
