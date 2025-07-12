# Run this in Django shell: python manage.py shell

from django.contrib.auth.models import User
from authentication.models import Organizer
from event_management.models import Event, Category, TicketType, PlatformPlan
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# 1. Create a test user (customer who will buy tickets)
user = User.objects.create_user(
    username='testbuyer',
    email='buyer@test.com',
    password='testpass123',
    first_name='John',
    last_name='Customer'
)
print(f"✅ Created customer: {user.username}")

# 2. Create an organizer account
organizer_user = User.objects.create_user(
    username='testorganizer',
    email='organizer@test.com',
    password='testpass123',
    first_name='Jane',
    last_name='Organizer'
)

organizer = Organizer.objects.create(
    user=organizer_user,
    company_name='Test Events Ltd',
    business_email='organizer@test.com',
    phone_number='+44 1234 567890',
    is_verified=True,
    payment_ready=True,
    paypal_email='organizer@paypal.com'
)
print(f"✅ Created organizer: {organizer.company_name}")

# 3. Create a category
category = Category.objects.create(
    name='Music',
    slug='music',
    description='Live music events'
)
print(f"✅ Created category: {category.name}")

# 4. Create a platform plan
platform_plan = PlatformPlan.objects.create(
    name='Basic Plan',
    price_per_event=Decimal('25.00'),
    max_tickets=100,
    is_active=True,
    description='Perfect for small events'
)
print(f"✅ Created platform plan: {platform_plan.name}")

# 5. Create a test event
event_date = timezone.now() + timedelta(days=30)  # Event in 30 days
event = Event.objects.create(
    title='Jersey Music Festival 2025',
    slug='jersey-music-festival-2025',
    description='An amazing music festival featuring local and international artists. Join us for a night of incredible music, food, and fun!',
    organizer=organizer,
    category=category,
    date=event_date,
    venue='Liberation Square',
    address='Liberation Square, St Helier, Jersey JE2 3NN',
    price=Decimal('45.00'),  # Default ticket price
    capacity=500,
    is_active=True,
    is_approved=True,
    is_featured=True,
    pet_friendly=False,
    family_friendly=True,
    platform_plan=platform_plan,
    plan_paid=True,
    paid_at=timezone.now(),
    status='approved'
)
print(f"✅ Created event: {event.title}")

# 6. Create ticket types for the event
ticket_types = [
    {
        'name': 'Early Bird',
        'price': Decimal('35.00'),
        'quantity': 100,
        'description': 'Limited early bird tickets with 22% discount!'
    },
    {
        'name': 'General Admission', 
        'price': Decimal('45.00'),
        'quantity': 300,
        'description': 'Standard entry to the festival'
    },
    {
        'name': 'VIP Experience',
        'price': Decimal('85.00'), 
        'quantity': 50,
        'description': 'VIP area access, complimentary drinks, and meet & greet'
    }
]

for ticket_data in ticket_types:
    ticket_type = TicketType.objects.create(
        event=event,
        name=ticket_data['name'],
        price=ticket_data['price'],
        quantity_available=ticket_data['quantity'],
        description=ticket_data['description'],
        sale_starts=timezone.now(),
        sale_ends=event_date - timedelta(hours=2)  # Sales end 2 hours before event
    )
    print(f"✅ Created ticket type: {ticket_type.name} - £{ticket_type.price}")

print("\n🎉 Test data created successfully!")
print("\n📝 Login credentials:")
print("Customer: testbuyer / testpass123")
print("Organizer: testorganizer / testpass123")
print(f"\n🎫 Event URL: /events/{event.slug}/")
print(f"🛒 Cart URL: /booking/cart/")
print(f"💳 Checkout URL: /booking/checkout/")

# Display some useful info
print(f"\n📊 Event Details:")
print(f"- Title: {event.title}")
print(f"- Date: {event.date.strftime('%B %d, %Y at %I:%M %p')}")
print(f"- Venue: {event.venue}")
print(f"- Capacity: {event.capacity}")
print(f"- Ticket Types: {event.ticket_types.count()}")
print(f"- Status: {event.status}")
print(f"- Approved: {event.is_approved}")
