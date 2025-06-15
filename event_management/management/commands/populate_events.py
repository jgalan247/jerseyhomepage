from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from datetime import datetime, timedelta
from decimal import Decimal
import random
from event_management.models import Event, Category
from authentication.models import Organizer, User

class Command(BaseCommand):
    help = 'Populate database with test events for all categories and filters'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating test events...')
        
        # Get or create a default organizer
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@jersey.live',
                password='admin123'
            )
        
        organizer, created = Organizer.objects.get_or_create(
        user=admin_user,
        defaults={
            'company_name': 'Jersey Events Ltd',
            'company_registration': 'JE123456',
            'vat_number': 'JE12345678',
            'business_email': 'events@jersey.live',
            'business_phone': '+44 1534 123456',
            'website': 'https://jersey.live',
            'address_line_1': '1 Liberation Square',
            'address_line_2': '',
            'city': 'St Helier',
            'parish': 'St Helier',
            'postal_code': 'JE2 3AB',
            'stripe_account_id': '',
            'stripe_onboarding_complete': False,
            'is_verified': True,
            'commission_rate': Decimal('10.00'),
            'description': 'Jersey\'s premier event management company',
            'facebook': 'jerseyevents',
            'instagram': 'jerseyevents',
            'twitter': 'jerseyevents',
         }
        )

        if created:
            self.stdout.write('Created new organizer: Jersey Events Ltd')
        else:
            self.stdout.write('Using existing organizer')
        
        # Ensure categories exist
        categories = Category.objects.all()
        if not categories:
            self.stdout.write(self.style.ERROR('No categories found! Run migrations first.'))
            return
        
        # Clear existing events (optional)
        if Event.objects.exists():
            self.stdout.write('Clearing existing events...')
            Event.objects.all().delete()
        
        # Event templates for each category
        events_data = {
            'things-to-do': [
                {
                    'title': 'Jersey Heritage Pass Tour',
                    'description': 'Explore Jersey\'s historic castles and museums with our exclusive heritage pass. Visit Mont Orgueil Castle, Elizabeth Castle, and the Jersey Museum.',
                    'venue': 'Various Heritage Sites',
                    'address': 'St Helier, Jersey',
                    'price': Decimal('25.00'),
                    'capacity': 50,
                    'family_friendly': True,
                    'pet_friendly': False,
                    'has_offers': True,
                },
                {
                    'title': 'Beach Yoga Sessions',
                    'description': 'Start your day with energizing yoga on the beautiful beaches of Jersey. Suitable for all levels.',
                    'venue': 'St Brelade\'s Bay',
                    'address': 'St Brelade\'s Bay, Jersey',
                    'price': Decimal('0.00'),  # Free event
                    'capacity': 30,
                    'family_friendly': True,
                    'pet_friendly': True,
                    'has_offers': False,
                },
                {
                    'title': 'Guided Coastal Walk',
                    'description': 'Join our experienced guides for a scenic walk along Jersey\'s stunning coastline. Learn about local wildlife and history.',
                    'venue': 'Corbière Lighthouse',
                    'address': 'La Corbière, St Brelade, Jersey',
                    'price': Decimal('15.00'),
                    'capacity': 20,
                    'family_friendly': True,
                    'pet_friendly': True,
                    'has_offers': False,
                },
            ],
            'arts-culture': [
                {
                    'title': 'Contemporary Art Exhibition',
                    'description': 'Featuring works by local and international artists exploring themes of island identity and modern life.',
                    'venue': 'Jersey Arts Centre',
                    'address': 'Phillips Street, St Helier, Jersey',
                    'price': Decimal('12.00'),
                    'capacity': 100,
                    'family_friendly': True,
                    'pet_friendly': False,
                    'has_offers': True,
                },
                {
                    'title': 'Photography Workshop',
                    'description': 'Learn landscape photography techniques with professional photographer. Camera required.',
                    'venue': 'Liberation Square',
                    'address': 'Liberation Square, St Helier, Jersey',
                    'price': Decimal('45.00'),
                    'capacity': 15,
                    'family_friendly': False,
                    'pet_friendly': False,
                    'has_offers': False,
                },
                {
                    'title': 'Theatre: Shakespeare by the Sea',
                    'description': 'Outdoor performance of Much Ado About Nothing. Bring your own chair or blanket.',
                    'venue': 'Gorey Harbour',
                    'address': 'Gorey, Grouville, Jersey',
                    'price': Decimal('0.00'),  # Free event
                    'capacity': 200,
                    'family_friendly': True,
                    'pet_friendly': True,
                    'has_offers': False,
                },
            ],
            'music': [
                {
                    'title': 'Jazz in the Park',
                    'description': 'Enjoy an evening of smooth jazz in the beautiful Howard Davis Park. Food and drinks available.',
                    'venue': 'Howard Davis Park',
                    'address': 'Don Road, St Helier, Jersey',
                    'price': Decimal('0.00'),  # Free event
                    'capacity': 300,
                    'family_friendly': True,
                    'pet_friendly': True,
                    'has_offers': False,
                },
                {
                    'title': 'Rock Concert: Local Bands Showcase',
                    'description': 'Support Jersey\'s music scene with performances from five local rock bands.',
                    'venue': 'Fort Regent',
                    'address': 'Fort Regent, St Helier, Jersey',
                    'price': Decimal('20.00'),
                    'capacity': 500,
                    'family_friendly': False,
                    'pet_friendly': False,
                    'has_offers': True,
                },
                {
                    'title': 'Classical Concert: Jersey Symphony Orchestra',
                    'description': 'An evening of Mozart and Beethoven performed by Jersey\'s finest musicians.',
                    'venue': 'Jersey Opera House',
                    'address': 'Gloucester Street, St Helier, Jersey',
                    'price': Decimal('35.00'),
                    'capacity': 400,
                    'family_friendly': True,
                    'pet_friendly': False,
                    'has_offers': True,
                },
            ],
            'food-and-drink': [
                {
                    'title': 'Jersey Food Festival',
                    'description': 'Celebrate Jersey\'s culinary scene with local producers, chef demonstrations, and tastings.',
                    'venue': 'Royal Square',
                    'address': 'Royal Square, St Helier, Jersey',
                    'price': Decimal('5.00'),
                    'capacity': 1000,
                    'family_friendly': True,
                    'pet_friendly': True,
                    'has_offers': False,
                },
                {
                    'title': 'Wine Tasting Evening',
                    'description': 'Sample premium wines from around the world with expert sommelier guidance.',
                    'venue': 'Grand Jersey Hotel',
                    'address': 'The Esplanade, St Helier, Jersey',
                    'price': Decimal('55.00'),
                    'capacity': 40,
                    'family_friendly': False,
                    'pet_friendly': False,
                    'has_offers': True,
                },
                {
                    'title': 'Farmers Market',
                    'description': 'Fresh local produce, artisan foods, and handmade crafts every Saturday morning.',
                    'venue': 'Central Market',
                    'address': 'Halkett Place, St Helier, Jersey',
                    'price': Decimal('0.00'),  # Free entry
                    'capacity': 500,
                    'family_friendly': True,
                    'pet_friendly': True,
                    'has_offers': False,
                },
            ],
            'outdoor-activities': [
                {
                    'title': 'Kayaking Adventure',
                    'description': 'Explore Jersey\'s hidden caves and beaches by kayak. All equipment provided.',
                    'venue': 'St Catherine\'s Bay',
                    'address': 'St Catherine\'s Bay, Jersey',
                    'price': Decimal('45.00'),
                    'capacity': 12,
                    'family_friendly': True,
                    'pet_friendly': False,
                    'has_offers': True,
                },
                {
                    'title': 'Mountain Biking Tour',
                    'description': 'Challenging trails through Jersey\'s countryside. Bike rental available.',
                    'venue': 'Les Landes',
                    'address': 'Les Landes, Jersey',
                    'price': Decimal('30.00'),
                    'capacity': 20,
                    'family_friendly': False,
                    'pet_friendly': False,
                    'has_offers': False,
                },
                {
                    'title': 'Surfing Lessons',
                    'description': 'Learn to surf with qualified instructors. Wetsuit and board included.',
                    'venue': 'St Ouen\'s Bay',
                    'address': 'St Ouen\'s Bay, Jersey',
                    'price': Decimal('40.00'),
                    'capacity': 8,
                    'family_friendly': True,
                    'pet_friendly': False,
                    'has_offers': True,
                },
            ],
            'sports': [
                {
                    'title': 'Jersey Marathon 2025',
                    'description': 'Annual marathon event with full, half, and relay options. Scenic route around the island.',
                    'venue': 'St Helier',
                    'address': 'Start: Liberation Square, St Helier, Jersey',
                    'price': Decimal('45.00'),
                    'capacity': 2000,
                    'family_friendly': True,
                    'pet_friendly': False,
                    'has_offers': True,
                },
                {
                    'title': 'Beach Volleyball Tournament',
                    'description': 'Open tournament for all skill levels. Teams of 4, prizes for winners.',
                    'venue': 'Havre des Pas',
                    'address': 'Havre des Pas, St Helier, Jersey',
                    'price': Decimal('20.00'),
                    'capacity': 100,
                    'family_friendly': True,
                    'pet_friendly': True,
                    'has_offers': False,
                },
                {
                    'title': 'Kids Football Camp',
                    'description': 'Professional coaching for children aged 6-12. All abilities welcome.',
                    'venue': 'FB Playing Fields',
                    'address': 'Plat Douet Road, St Clement, Jersey',
                    'price': Decimal('0.00'),  # Free event
                    'capacity': 60,
                    'family_friendly': True,
                    'pet_friendly': False,
                    'has_offers': False,
                },
            ],
            'mindfulness-and-wellbeing': [
                {
                    'title': 'Meditation Workshop',
                    'description': 'Learn mindfulness techniques for stress relief and mental clarity.',
                    'venue': 'Samares Manor',
                    'address': 'Samares Manor, St Clement, Jersey',
                    'price': Decimal('25.00'),
                    'capacity': 25,
                    'family_friendly': False,
                    'pet_friendly': False,
                    'has_offers': True,
                },
                {
                    'title': 'Wellness Retreat Day',
                    'description': 'Full day retreat including yoga, meditation, healthy lunch, and spa access.',
                    'venue': 'L\'Horizon Beach Hotel',
                    'address': 'St Brelade\'s Bay, Jersey',
                    'price': Decimal('120.00'),
                    'capacity': 30,
                    'family_friendly': False,
                    'pet_friendly': False,
                    'has_offers': True,
                },
                {
                    'title': 'Community Tai Chi',
                    'description': 'Gentle exercise suitable for all ages. Improve balance and flexibility.',
                    'venue': 'Millennium Park',
                    'address': 'St Helier, Jersey',
                    'price': Decimal('0.00'),  # Free event
                    'capacity': 50,
                    'family_friendly': True,
                    'pet_friendly': True,
                    'has_offers': False,
                },
            ],
        }
        
        # Create events
        created_count = 0
        now = timezone.now()
        
        for category_slug, events_list in events_data.items():
            try:
                category = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Category {category_slug} not found, skipping...'))
                continue
            
            for event_data in events_list:
                # Create multiple instances with different dates
                for i in range(3):  # Create 3 instances of each event
                    # Vary the dates
                    if i == 0:
                        # This week
                        days_ahead = random.randint(1, 7)
                    elif i == 1:
                        # Next 2 weeks  
                        days_ahead = random.randint(8, 21)
                    else:
                        # Next month
                        days_ahead = random.randint(22, 45)
                    
                    # Make some events on weekends
                    event_date = now + timedelta(days=days_ahead)
                    if random.choice([True, False]):
                        # Move to weekend
                        days_to_saturday = (5 - event_date.weekday()) % 7
                        if days_to_saturday == 0:
                            days_to_saturday = 7
                        event_date += timedelta(days=days_to_saturday)
                    
                    # Set time
                    hour = random.choice([10, 14, 16, 19, 20])
                    event_date = event_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    
                    # Create unique slug
                    base_slug = slugify(event_data['title'])
                    date_str = event_date.strftime('%Y%m%d')
                    unique_slug = f"{base_slug}-{date_str}-{i}"
                    
                    # Vary prices for some events
                    price = event_data['price']
                    if price > 0 and i == 2:
                        # Last instance might have a different price
                        price = price * Decimal('0.8')  # 20% discount
                    
                    # Create the event
                    event = Event.objects.create(
                        title=event_data['title'],
                        slug=unique_slug,
                        description=event_data['description'],
                        venue=event_data['venue'],
                        address=event_data['address'],
                        date=event_date,
                        category=category,
                        price=price,
                        capacity=event_data['capacity'],
                        tickets_sold=random.randint(0, int(event_data['capacity'] * 0.7)),
                        organizer=organizer,
                        is_featured=random.choice([True, False, False]),  # 33% chance
                        is_active=True,
                        pet_friendly=event_data['pet_friendly'],
                        family_friendly=event_data['family_friendly'],
                        has_offers=event_data['has_offers'],
                    )
                    
                    created_count += 1
                    
        # Create a few past events (for testing date filters)
        for i in range(5):
            past_date = now - timedelta(days=random.randint(1, 30))
            category = random.choice(categories)
            
            Event.objects.create(
                title=f"Past Event {i+1}",
                slug=f"past-event-{i+1}",
                description="This is a past event for testing purposes.",
                venue="Test Venue",
                address="St Helier, Jersey",
                date=past_date,
                category=category,
                price=Decimal('10.00'),
                capacity=50,
                organizer=organizer,
                is_active=True,
                pet_friendly=False,
                family_friendly=True,
                has_offers=False,
            )
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} events!'))
        
        # Print summary
        self.stdout.write('\nEvent Summary:')
        self.stdout.write(f'Total events: {Event.objects.count()}')
        self.stdout.write(f'Free events: {Event.objects.filter(price=0).count()}')
        self.stdout.write(f'Events with offers: {Event.objects.filter(has_offers=True).count()}')
        self.stdout.write(f'Family friendly: {Event.objects.filter(family_friendly=True).count()}')
        self.stdout.write(f'Pet friendly: {Event.objects.filter(pet_friendly=True).count()}')
        self.stdout.write(f'Weekend events: {Event.objects.filter(date__week_day__in=[6, 7, 1]).count()}')
        
        for category in categories:
            count = Event.objects.filter(category=category).count()
            self.stdout.write(f'{category.name}: {count} events')