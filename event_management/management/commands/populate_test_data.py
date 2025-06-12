# event_management/management/commands/populate_test_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from event_management.models import Category, Event, EventImage
from datetime import timedelta
from decimal import Decimal
import random
from faker import Faker

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Populate database with test data for events platform'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data population...')
        
        # Create users
        self.create_users()
        
        # Create categories
        self.create_categories()
        
        # Create events
        self.create_events()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated test data!'))
        self.print_summary()

    def create_users(self):
        """Create different types of users"""
        
        # Create superuser if doesn't exist
        if not User.objects.filter(email='admin@jersey.live').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@jersey.live',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write('Created superuser: admin@jersey.live / admin123')
        
        # Create event organizers
        organizers_data = [
            {'username': 'jersey_events', 'email': 'events@jersey.live', 'first_name': 'Jersey', 'last_name': 'Events'},
            {'username': 'culture_jersey', 'email': 'culture@jersey.live', 'first_name': 'Culture', 'last_name': 'Jersey'},
            {'username': 'foodie_jersey', 'email': 'food@jersey.live', 'first_name': 'Foodie', 'last_name': 'Jersey'},
            {'username': 'entertainment_co', 'email': 'entertainment@jersey.live', 'first_name': 'Entertainment', 'last_name': 'Company'},
        ]
        
        for org_data in organizers_data:
            if not User.objects.filter(email=org_data['email']).exists():
                user = User.objects.create_user(
                    username=org_data['username'],
                    email=org_data['email'],
                    password='organizer123',
                    first_name=org_data['first_name'],
                    last_name=org_data['last_name'],
                    is_verified=True
                )
                self.stdout.write(f'Created organizer: {user.email}')
        
        # Create regular users (some verified, some not)
        for i in range(10):
            email = f'user{i}@example.com'
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=f'user{i}',
                    email=email,
                    password='user123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    is_verified=random.choice([True, True, True, False]),  # 75% verified
                    phone=fake.phone_number()[:20],
                    newsletter_subscription=random.choice([True, False])
                )
                self.stdout.write(f'Created user: {user.email} (verified: {user.is_verified})')

    def create_categories(self):
        """Create event categories"""
        categories_data = [
            {
                'name': 'Food & Drink',
                'slug': 'food-drink',
                'icon': 'utensils',
                'color': '#F59E0B'
            },
            {
                'name': 'Theatre & Films',
                'slug': 'theatre-films',
                'icon': 'film',
                'color': '#8B5CF6'
            },
            {
                'name': 'Art & Culture',
                'slug': 'art-culture',
                'icon': 'palette',
                'color': '#10B981'
            },
            {
                'name': 'Things to Do',
                'slug': 'things-to-do',
                'icon': 'calendar',
                'color': '#3B82F6'
            },
            {
                'name': 'Music & Concerts',
                'slug': 'music-concerts',
                'icon': 'music',
                'color': '#EC4899'
            },
            {
                'name': 'Sports & Fitness',
                'slug': 'sports-fitness',
                'icon': 'running',
                'color': '#14B8A6'
            }
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_events(self):
        """Create diverse events for testing"""
        
        # Get all categories and organizers
        categories = Category.objects.all()
        organizers = User.objects.filter(email__contains='jersey.live').exclude(email='admin@jersey.live')
        
        # Event templates for realistic data
        event_templates = {
            'food-drink': [
                {
                    'title': 'Craft Beer & Street Food Festival',
                    'description': 'Sample the best craft beers from local breweries paired with delicious street food from Jersey\'s top vendors. Live music throughout the day!',
                    'venue': 'People\'s Park',
                    'address': 'St. Helier, Jersey JE2 3JA',
                    'price': Decimal('5.00'),
                    'capacity': 1000,
                    'pet_friendly': True,
                    'family_friendly': True,
                },
                {
                    'title': 'Wine Tasting Evening',
                    'description': 'Join us for an exclusive wine tasting experience featuring wines from around the world. Expert sommeliers will guide you through each tasting.',
                    'venue': 'La Mare Wine Estate',
                    'address': 'St. Mary, Jersey JE3 3BA',
                    'price': Decimal('45.00'),
                    'capacity': 50,
                    'pet_friendly': False,
                    'family_friendly': False,
                },
                {
                    'title': 'Jersey Food Festival',
                    'description': 'Celebrate Jersey\'s culinary excellence with local producers, chef demonstrations, and tastings.',
                    'venue': 'Royal Square',
                    'address': 'St. Helier, Jersey JE2 4WQ',
                    'price': Decimal('0.00'),  # Free event
                    'capacity': 2000,
                    'pet_friendly': True,
                    'family_friendly': True,
                },
                {
                    'title': 'Cocktail Masterclass',
                    'description': 'Learn to make classic cocktails with our expert mixologists. All equipment and ingredients provided.',
                    'venue': 'The Drift Bar',
                    'address': 'St. Helier, Jersey JE2 3QA',
                    'price': Decimal('35.00'),
                    'capacity': 20,
                    'pet_friendly': False,
                    'family_friendly': False,
                },
            ],
            'theatre-films': [
                {
                    'title': 'Shakespeare in the Park: Hamlet',
                    'description': 'Experience Shakespeare\'s masterpiece performed under the stars by the Jersey Shakespeare Company.',
                    'venue': 'Howard Davis Park',
                    'address': 'St. Saviour, Jersey JE2 7XH',
                    'price': Decimal('20.00'),
                    'capacity': 200,
                    'pet_friendly': False,
                    'family_friendly': True,
                },
                {
                    'title': 'Comedy Night at the Opera House',
                    'description': 'Top UK comedians bring their best material for a night of non-stop laughter.',
                    'venue': 'Jersey Opera House',
                    'address': 'Gloucester Street, St. Helier JE2 3QR',
                    'price': Decimal('25.00'),
                    'capacity': 600,
                    'pet_friendly': False,
                    'family_friendly': False,
                },
                {
                    'title': 'Kids Theatre: The Gruffalo',
                    'description': 'A delightful adaptation of the beloved children\'s book, perfect for ages 3-8.',
                    'venue': 'Jersey Arts Centre',
                    'address': 'Phillips Street, St. Helier JE2 4SW',
                    'price': Decimal('12.00'),
                    'capacity': 150,
                    'pet_friendly': False,
                    'family_friendly': True,
                },
            ],
            'art-culture': [
                {
                    'title': 'Contemporary Art Exhibition Opening',
                    'description': 'Opening night of our new exhibition featuring local and international artists.',
                    'venue': 'Jersey Museum & Art Gallery',
                    'address': 'The Weighbridge, St. Helier JE2 3NG',
                    'price': Decimal('0.00'),  # Free event
                    'capacity': 150,
                    'pet_friendly': False,
                    'family_friendly': True,
                },
                {
                    'title': 'Photography Workshop: Landscape',
                    'description': 'Learn landscape photography techniques with professional photographer. Camera required.',
                    'venue': 'St. Brelade\'s Bay',
                    'address': 'St. Brelade, Jersey JE3 8EF',
                    'price': Decimal('75.00'),
                    'capacity': 15,
                    'pet_friendly': True,
                    'family_friendly': False,
                },
            ],
            'things-to-do': [
                {
                    'title': 'Coastal Walk & Wildlife Tour',
                    'description': 'Guided walk along Jersey\'s stunning coastline with wildlife expert. Spot seabirds and marine life.',
                    'venue': 'St. Catherine\'s Breakwater',
                    'address': 'St. Martin, Jersey JE3 6DS',
                    'price': Decimal('15.00'),
                    'capacity': 30,
                    'pet_friendly': True,
                    'family_friendly': True,
                },
                {
                    'title': 'Historical Tour of Mont Orgueil Castle',
                    'description': 'Discover 800 years of history with our expert guides. Includes castle admission.',
                    'venue': 'Mont Orgueil Castle',
                    'address': 'Gorey, St. Martin JE3 6ET',
                    'price': Decimal('18.00'),
                    'capacity': 40,
                    'pet_friendly': False,
                    'family_friendly': True,
                },
            ],
            'music-concerts': [
                {
                    'title': 'Jazz on the Beach',
                    'description': 'Smooth jazz performances as the sun sets over St. Brelade\'s Bay. Bring a picnic!',
                    'venue': 'St. Brelade\'s Beach',
                    'address': 'St. Brelade, Jersey JE3 8LQ',
                    'price': Decimal('0.00'),  # Free event
                    'capacity': 500,
                    'pet_friendly': True,
                    'family_friendly': True,
                },
                {
                    'title': 'Rock Concert: Local Bands Showcase',
                    'description': 'Jersey\'s best rock bands compete for the title. High energy performances all night!',
                    'venue': 'Fort Regent',
                    'address': 'St. Helier, Jersey JE2 4UH',
                    'price': Decimal('15.00'),
                    'capacity': 800,
                    'pet_friendly': False,
                    'family_friendly': False,
                },
            ],
            'sports-fitness': [
                {
                    'title': 'Beach Yoga at Sunrise',
                    'description': 'Start your day with energizing yoga on the beach. All levels welcome. Mats provided.',
                    'venue': 'St. Ouen\'s Bay',
                    'address': 'St. Ouen, Jersey JE3 2GJ',
                    'price': Decimal('10.00'),
                    'capacity': 25,
                    'pet_friendly': False,
                    'family_friendly': True,
                },
                {
                    'title': 'Jersey Marathon 2025',
                    'description': 'Annual marathon event around the island. Full marathon, half marathon, and relay options.',
                    'venue': 'Liberation Square',
                    'address': 'St. Helier, Jersey JE1 1BB',
                    'price': Decimal('45.00'),
                    'capacity': 2000,
                    'pet_friendly': False,
                    'family_friendly': True,
                },
            ]
        }
        
        # Create events
        for category in categories:
            if category.slug in event_templates:
                templates = event_templates[category.slug]
                
                for i, template in enumerate(templates):
                    # Create multiple time variations for some events
                    for j in range(random.randint(1, 3)):
                        # Generate event date (some past, mostly future)
                        if random.random() < 0.1:  # 10% past events
                            days_offset = random.randint(-30, -1)
                        else:  # 90% future events
                            days_offset = random.randint(1, 90)
                        
                        event_date = timezone.now() + timedelta(days=days_offset)
                        
                        # Some events on weekends
                        if random.random() < 0.6:  # 60% on weekends
                            days_to_weekend = (5 - event_date.weekday()) % 7
                            if days_to_weekend == 0:
                                days_to_weekend = 7
                            event_date += timedelta(days=days_to_weekend)
                        
                        # Set event time
                        hour = random.choice([10, 14, 18, 19, 20])  # Morning, afternoon, or evening
                        event_date = event_date.replace(hour=hour, minute=0, second=0)
                        
                        # Create unique title for multiple instances
                        title = template['title']
                        if j > 0:
                            title = f"{title} - {event_date.strftime('%B %d')}"
                        
                        # Create slug
                        slug = slugify(f"{title}-{event_date.strftime('%Y%m%d')}")
                        
                        # Random organizer
                        organizer = random.choice(organizers)
                        
                        # Create event
                        event, created = Event.objects.get_or_create(
                            slug=slug,
                            defaults={
                                'title': title,
                                'description': template['description'],
                                'venue': template['venue'],
                                'address': template['address'],
                                'date': event_date,
                                'end_date': event_date + timedelta(hours=random.randint(2, 4)),
                                'category': category,
                                'price': template['price'],
                                'capacity': template['capacity'],
                                'tickets_sold': random.randint(0, int(template['capacity'] * 0.8)),
                                'organizer': organizer,
                                'is_featured': random.random() < 0.2,  # 20% featured
                                'is_active': True,
                                'pet_friendly': template.get('pet_friendly', False),
                                'family_friendly': template.get('family_friendly', True),
                            }
                        )
                        
                        if created:
                            self.stdout.write(f'Created event: {event.title} on {event.date.strftime("%Y-%m-%d")}')
        
        # Create some sold out events
        sold_out_events = Event.objects.filter(is_active=True).order_by('?')[:3]
        for event in sold_out_events:
            event.tickets_sold = event.capacity
            event.save()
            self.stdout.write(f'Made event sold out: {event.title}')

    def print_summary(self):
        """Print summary of created data"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('DATA SUMMARY:')
        self.stdout.write('='*50)
        
        # Users
        total_users = User.objects.count()
        verified_users = User.objects.filter(is_verified=True).count()
        self.stdout.write(f'\nUSERS:')
        self.stdout.write(f'  Total users: {total_users}')
        self.stdout.write(f'  Verified users: {verified_users}')
        self.stdout.write(f'  Unverified users: {total_users - verified_users}')
        
        # Categories
        self.stdout.write(f'\nCATEGORIES:')
        for category in Category.objects.all():
            event_count = category.events.count()
            self.stdout.write(f'  {category.name}: {event_count} events')
        
        # Events
        total_events = Event.objects.count()
        upcoming_events = Event.objects.filter(date__gte=timezone.now()).count()
        past_events = Event.objects.filter(date__lt=timezone.now()).count()
        free_events = Event.objects.filter(price=0).count()
        sold_out_events = Event.objects.filter(tickets_sold__gte=models.F('capacity')).count()
        
        self.stdout.write(f'\nEVENTS:')
        self.stdout.write(f'  Total events: {total_events}')
        self.stdout.write(f'  Upcoming events: {upcoming_events}')
        self.stdout.write(f'  Past events: {past_events}')
        self.stdout.write(f'  Free events: {free_events}')
        self.stdout.write(f'  Sold out events: {sold_out_events}')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TEST ACCOUNTS:')
        self.stdout.write('='*50)
        self.stdout.write('Admin: admin@jersey.live / admin123')
        self.stdout.write('Organizers: events@jersey.live, culture@jersey.live, food@jersey.live / organizer123')
        self.stdout.write('Users: user0@example.com to user9@example.com / user123')
        self.stdout.write('='*50 + '\n')