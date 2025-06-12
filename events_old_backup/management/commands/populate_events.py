from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import Category, Event
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate sample events data'

    def handle(self, *args, **kwargs):
        # Create categories
        categories_data = [
            {'name': 'Food & Drink', 'slug': 'food-drink', 'icon': 'utensils', 'color': '#F59E0B'},
            {'name': 'Theatre & Films', 'slug': 'theatre-films', 'icon': 'film', 'color': '#8B5CF6'},
            {'name': 'Art & Culture', 'slug': 'art-culture', 'icon': 'palette', 'color': '#10B981'},
            {'name': 'Things to Do', 'slug': 'things-to-do', 'icon': 'calendar', 'color': '#3B82F6'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Get or create organizer
        organizer = User.objects.first()
        if not organizer:
            organizer = User.objects.create_user(
                'organizer', 
                'organizer@example.com', 
                'password123'
            )
        
        # Sample events data
        events_data = [
            {
                'title': 'Craft Beer & Street Food Festival',
                'category': 'food-drink',
                'venue': "People's Park",
                'address': 'St. Helier, Jersey',
                'description': 'Sample local craft beers and delicious street food from Jersey\'s best vendors.',
                'price': 5.00,
                'capacity': 1000,
            },
            {
                'title': 'Shakespeare in the Park',
                'category': 'theatre-films',
                'venue': 'Howard Davis Park',
                'address': 'St. Saviour, Jersey',
                'description': 'Outdoor performance of "A Midsummer Night\'s Dream" by Jersey Shakespeare Company.',
                'price': 20.00,
                'capacity': 200,
                'family_friendly': True,
            },
            {
                'title': 'Jersey Art Gallery Opening',
                'category': 'art-culture',
                'venue': 'Jersey Arts Centre',
                'address': 'Phillips Street, St. Helier',
                'description': 'Opening night of contemporary art exhibition featuring local artists.',
                'price': 0.00,
                'capacity': 150,
            },
            {
                'title': 'Coastal Walk & Wildlife Tour',
                'category': 'things-to-do',
                'venue': 'St. Brelade\'s Bay',
                'address': 'St. Brelade, Jersey',
                'description': 'Guided walk along Jersey\'s beautiful coastline with wildlife expert.',
                'price': 15.00,
                'capacity': 30,
                'pet_friendly': True,
                'family_friendly': True,
            },
            {
                'title': 'Wine Tasting Evening',
                'category': 'food-drink',
                'venue': 'La Mare Wine Estate',
                'address': 'St. Mary, Jersey',
                'description': 'Sample award-winning wines and learn about wine production in Jersey.',
                'price': 35.00,
                'capacity': 50,
            },
            {
                'title': 'Comedy Night at the Opera House',
                'category': 'theatre-films',
                'venue': 'Jersey Opera House',
                'address': 'Gloucester Street, St. Helier',
                'description': 'Stand-up comedy featuring top UK comedians.',
                'price': 25.00,
                'capacity': 600,
            },
        ]
        
        # Create events
        for event_data in events_data:
            # Get category
            category_slug = event_data.pop('category')
            category = Category.objects.get(slug=category_slug)
            
            # Generate random future date
            days_ahead = random.randint(1, 60)
            event_date = timezone.now() + timedelta(days=days_ahead)
            
            # Create slug from title
            from django.utils.text import slugify
            slug = slugify(event_data['title'])
            
            # Create event
            event, created = Event.objects.get_or_create(
                slug=slug,
                defaults={
                    **event_data,
                    'category': category,
                    'date': event_date,
                    'organizer': organizer,
                    'price': Decimal(str(event_data.get('price', 0))),
                    'is_featured': random.choice([True, False]),
                    'tickets_sold': random.randint(0, event_data['capacity'] // 2),
                }
            )
            
            if created:
                self.stdout.write(f'Created event: {event.title}')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated events data'))