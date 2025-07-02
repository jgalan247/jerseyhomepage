from django import forms
from .models import Event, EventImage
from django.utils.text import slugify
from django.utils import timezone

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'venue', 'address', 
            'date', 'end_date', 'image', 'category', 
            'price', 'capacity', 'pet_friendly', 'family_friendly'
        ]
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class EventImageForm(forms.ModelForm):
    class Meta:
        model = EventImage
        fields = ['image', 'caption']

class EventSubmissionForm(forms.ModelForm):
    """Form for organizers to submit new events"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'venue', 'address',
            'date', 'end_date', 'price', 'capacity', 
            'category', 'image', 'pet_friendly', 'family_friendly'
        ]
        widgets = {
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'min': timezone.now().strftime('%Y-%m-%dT%H:%M'),
                'class': 'form-control'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Describe your event in detail...'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event title'
            }),
            'venue': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Venue name'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full address'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Maximum attendees'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event category'
            }),
        }
        labels = {
            'pet_friendly': 'Pet-friendly event',
            'family_friendly': 'Family-friendly event',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text
        self.fields['image'].help_text = 'Upload an event banner/image (optional)'
        self.fields['capacity'].help_text = 'Leave blank for unlimited capacity'
        self.fields['end_date'].help_text = 'When does your event end? (optional)'
        
        # Mark required fields
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['venue'].required = True
        self.fields['address'].required = True
        self.fields['date'].required = True
        self.fields['price'].required = True
        
        # Make some fields optional
        self.fields['end_date'].required = False
        self.fields['capacity'].required = False
        self.fields['category'].required = False
        self.fields['image'].required = False
        
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        end_date = cleaned_data.get('end_date')
        
        if date and date < timezone.now():
            raise forms.ValidationError("Event date must be in the future")
            
        if end_date and date and end_date < date:
            raise forms.ValidationError("End date must be after start date")
            
        return cleaned_data
    
    def save(self, commit=True):
        """Generate slug and set approval status"""
        event = super().save(commit=False)
        
        # Generate unique slug if new event
        if not event.pk:
            base_slug = slugify(event.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            event.slug = slug
            
            # New events start as unapproved and active
            event.is_approved = False
            event.is_active = True
            event.is_featured = False
            event.is_premium = False
            event.has_offers = False
            event.tickets_sold = 0
        
        if commit:
            event.save()
        return event


class EventEditForm(EventSubmissionForm):
    """Form for editing existing events - inherits from submission form"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For existing events, you might want to disable editing certain fields
        if self.instance.pk:
            # Example: Make title read-only for existing events
            # self.fields['title'].widget.attrs['readonly'] = True
            pass