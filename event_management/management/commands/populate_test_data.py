from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import F
from datetime import datetime, timedelta
import random
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with test data for development'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to populate test data...')
        
        # Create users and organizers
        self.create_users_and_organizers()
        
        # Create categories
        self.create_categories()
        
        # Create events
        self.create_events()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated test data!'))

    def create_users_and_organizers(self):
        from authentication.models import Organizer
        
        self.stdout.write('Creating users and organizers...')
        
        # Create organizers
        organizer_data = [
            {
                'user': {
                    'username': 'jerseyevents',
                    'email': 'events@jersey.live',
                    'first_name': 'Jersey',
                    'last_name': 'Events',
                    'phone_number': '+44 1534 100001',
                },
                'organizer': {
                    'company_name': 'Jersey Events Ltd',
                    'business_email': 'business@jerseyevents.je',
                    'business_phone': '+44 1534 123456',
                    'website': 'https://jerseyevents.je',
                    'address_line_1': '10 Royal Square',
                    'city': 'St Helier',
                    'parish': 'St Helier',
                    'postal_code': 'JE2 4WA',
                    'description': 'Jersey\'s premier event management company',
                    'commission_rate': 10.00,
                }
            },
            {
                'user': {
                    'username': 'summerfest',
                    'email': 'info@summerfest.je',
                    'first_name': 'Summer',
                    'last_name': 'Festival',
                    'phone_number': '+44 1534 100002',
                },
                'organizer': {
                    'company_name': 'Summer Festival Organizers',
                    'business_email': 'bookings@summerfest.je',
                    'business_phone': '+44 1534 234567',
                    'address_line_1': '25 Halkett Place',
                    'city': 'St Helier',
                    'parish': 'St Helier',
                    'postal_code': 'JE2 4WG',
                    'description': 'Bringing the best summer events to Jersey',
                    'commission_rate': 12.00,
                }
            }
        ]
        
        self.organizers = []
        for data in organizer_data:
            # Create or get user
            user, created = User.objects.get_or_create(
                username=data['user']['username'],
                defaults={
                    **data['user'],
                    'email_verified': True,
                }
            )
            
            if created:
                user.set_password('organizer123')
                user.save()
                self.stdout.write(f'Created user: {user.email}')
            
            # Create organizer profile
            organizer, created = Organizer.objects.get_or_create(
                user=user,
                defaults={
                    **data['organizer'],
                    'is_verified': True,
                    'verified_at': timezone.now(),
                }
            )
            
            if created:
                self.stdout.write(f'Created organizer: {organizer.company_name}')
            
            self.organizers.append(organizer)
        
        # Create regular users
        for i in range(10):
            username = f'user{i}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'user{i}@example.com',
                    password='user123',
                    first_name=f'User{i}',
                    last_name='TestUser',
                    phone_number=f'+44 1534 2000{i:02d}',
                    email_verified=True,
                )
                self.stdout.write(f'Created user: {user.email}')

    def create_categories(self):
        from event_management.models import Category
        
        self.stdout.write('Creating categories...')
        
        categories = [
            {'name': 'Music', 'slug': 'music'},
            {'name': 'Sports', 'slug': 'sports'},
            {'name': 'Arts & Culture', 'slug': 'arts-culture'},
            {'name': 'Food & Drink', 'slug': 'food-drink'},
            {'name': 'Comedy', 'slug': 'comedy'},
            {'name': 'Theater', 'slug': 'theater'},
            {'name': 'Family', 'slug': 'family'},
            {'name': 'Nightlife', 'slug': 'nightlife'},
        ]
        
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name']
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_events(self):
        from event_management.models import Event, Category
        from authentication.models import Organizer
        
        self.stdout.write('Creating events...')
        
        # Get categories
        categories = {
            'music': Category.objects.get(slug='music'),
            'sports': Category.objects.get(slug='sports'),
            'arts': Category.objects.get(slug='arts-culture'),
            'food': Category.objects.get(slug='food-drink'),
            'comedy': Category.objects.get(slug='comedy'),
            'theater': Category.objects.get(slug='theater'),
            'family': Category.objects.get(slug='family'),
            'nightlife': Category.objects.get(slug='nightlife'),
        }
        
        # Make sure we have organizers
        if not hasattr(self, 'organizers') or not self.organizers:
            self.organizers = list(Organizer.objects.filter(is_verified=True))
        
        if not self.organizers:
            self.stdout.write(self.style.ERROR('No organizers found! Please create organizers first.'))
            return
        
        events_data = [
            # Music Events
            {
                'title': 'Jersey Live 2025',
                'description': 'The biggest music festival in Jersey featuring international and local artists across multiple stages.',
                'category': categories['music'],
                'venue': 'Royal Jersey Showground',
                'address': 'La Route de la Trinité, Trinity, Jersey',
                'date_offset': 90,
                'price': Decimal('75.00'),
                'capacity': 10000,
                'tickets_sold': 3500
            },
            {
                'title': 'Jazz in the Park',
                'description': 'An evening of smooth jazz under the stars featuring local and visiting jazz musicians.',
                'category': categories['music'],
                'venue': 'Howard Davis Park',
                'address': 'St Saviour, Jersey',
                'date_offset': 30,
                'price': Decimal('25.00'),
                'capacity': 500,
                'tickets_sold': 200
            },
            {
                'title': 'Rock Night at Fort Regent',
                'description': 'Local rock bands battle it out in this epic rock music competition.',
                'category': categories['music'],
                'venue': 'Fort Regent',
                'address': 'St Helier, Jersey',
                'date_offset': 14,
                'price': Decimal('15.00'),
                'capacity': 800,
                'tickets_sold': 450
            },
            
            # Sports Events
            {
                'title': 'Jersey Marathon 2025',
                'description': 'The annual Jersey Marathon through the scenic countryside and coastal roads.',
                'category': categories['sports'],
                'venue': 'Starting at Liberation Square',
                'address': 'St Helier, Jersey',
                'date_offset': 120,
                'price': Decimal('45.00'),
                'capacity': 2000,
                'tickets_sold': 800
            },
            {
                'title': 'Beach Volleyball Championship',
                'description': 'Professional beach volleyball tournament at St Brelade\'s Bay.',
                'category': categories['sports'],
                'venue': 'St Brelade\'s Bay',
                'address': 'St Brelade, Jersey',
                'date_offset': 60,
                'price': Decimal('0.00'),
                'capacity': 1000,
                'tickets_sold': 0
            },
            
            # Food Events
            {
                'title': 'Jersey Food Festival',
                'description': 'Celebrate Jersey\'s culinary excellence with local producers, chefs, and restaurants.',
                'category': categories['food'],
                'venue': 'Weighbridge Place',
                'address': 'St Helier, Jersey',
                'date_offset': 45,
                'price': Decimal('12.00'),
                'capacity': 3000,
                'tickets_sold': 1200
            },
            {
                'title': 'Wine Tasting Evening',
                'description': 'Sample wines from around the world with expert sommeliers.',
                'category': categories['food'],
                'venue': 'Grand Jersey Hotel',
                'address': 'The Esplanade, St Helier',
                'date_offset': 7,
                'price': Decimal('35.00'),
                'capacity': 100,
                'tickets_sold': 75
            },
            
            # Comedy Events
            {
                'title': 'Comedy Club Night',
                'description': 'Stand-up comedy featuring UK touring comedians and local talent.',
                'category': categories['comedy'],
                'venue': 'Jersey Arts Centre',
                'address': 'Phillips Street, St Helier',
                'date_offset': 10,
                'price': Decimal('20.00'),
                'capacity': 200,
                'tickets_sold': 150
            },
            
            # Theater Events
            {
                'title': 'Shakespeare in the Gardens',
                'description': 'Outdoor performance of Romeo and Juliet in the beautiful Samares Manor Gardens.',
                'category': categories['theater'],
                'venue': 'Samares Manor',
                'address': 'St Clement, Jersey',
                'date_offset': 35,
                'price': Decimal('28.00'),
                'capacity': 400,
                'tickets_sold': 250
            },
            
            # Family Events
            {
                'title': 'Family Fun Day',
                'description': 'Activities, games, and entertainment for the whole family.',
                'category': categories['family'],
                'venue': 'Les Jardins de la Mer',
                'address': 'St Helier Waterfront',
                'date_offset': 20,
                'price': Decimal('0.00'),
                'capacity': 5000,
                'tickets_sold': 0
            },
            
            # Arts & Culture
            {
                'title': 'Art Gallery Opening Night',
                'description': 'New exhibition featuring contemporary Jersey artists.',
                'category': categories['arts'],
                'venue': 'CCA Gallery International',
                'address': 'Capital House, St Helier',
                'date_offset': 5,
                'price': Decimal('0.00'),
                'capacity': 150,
                'tickets_sold': 0
            }
        ]
        
        for event_info in events_data:
            # Check if event already exists
            if not Event.objects.filter(title=event_info['title']).exists():
                # Calculate event date
                event_date = timezone.now() + timedelta(days=event_info['date_offset'])
                
                # Select random organizer
                organizer = random.choice(self.organizers)
                
                event = Event.objects.create(
                    title=event_info['title'],
                    slug=event_info['title'].lower().replace(' ', '-'),
                    description=event_info['description'],
                    organizer=organizer.user,  # Use the user, not the organizer object
                    category=event_info['category'],
                    venue=event_info['venue'],
                    address=event_info['address'],
                    date=event_date,
                    price=event_info['price'],
                    capacity=event_info['capacity'],
                    is_active=True
                )
                
                # Update tickets_sold using F expression
                if event_info['tickets_sold'] > 0:
                    Event.objects.filter(pk=event.pk).update(
                        tickets_sold=F('tickets_sold') + event_info['tickets_sold']
                    )
                
                self.stdout.write(f'Created event: {event.title} (Organizer: {organizer.user.get_full_name()})')
        
        self.stdout.write(self.style.SUCCESS('All events created successfully!'))