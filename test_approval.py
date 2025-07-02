from django.test import Client
from django.contrib.auth import get_user_model
from event_management.models import Event
from django.urls import reverse

User = get_user_model()

# Create test clients
anonymous_client = Client()
staff_client = Client()

# Create staff user
staff_user = User.objects.create_user(
    username='stafftest',
    password='testpass123',
    is_staff=True
)
staff_client.login(username='stafftest', password='testpass123')

# Get an unapproved event (or create one for testing)
try:
    unapproved_event = Event.objects.filter(is_approved=False).first()
    if not unapproved_event:
        # Create one if none exists
        unapproved_event = Event.objects.create(
            name="Test Unapproved Event",
            slug="test-unapproved-event",
            description="Test event",
            location="St Helier",
            date="2025-07-01",
            time="19:00",
            price=10.00,
            is_approved=False
        )
        print(f"✅ Created test event: {unapproved_event.slug}")
except Exception as e:
    print(f"❌ Error creating test event: {e}")
    exit()

# Test anonymous access to unapproved event
print("\n🔍 Testing anonymous access to unapproved event...")
response = anonymous_client.get(reverse('event_detail', kwargs={'slug': unapproved_event.slug}))
if response.status_code == 404:
    print("✅ Anonymous user gets 404 for unapproved event - CORRECT")
else:
    print(f"❌ Anonymous user got {response.status_code} - SECURITY ISSUE!")

# Test staff access to unapproved event
print("\n🔍 Testing staff access to unapproved event...")
response = staff_client.get(reverse('event_detail', kwargs={'slug': unapproved_event.slug}))
if response.status_code == 200:
    print("✅ Staff can access unapproved event - CORRECT")
else:
    print(f"❌ Staff got {response.status_code} - INCORRECT")

# Test that unapproved events don't appear in public list
print("\n🔍 Testing public event list...")
response = anonymous_client.get(reverse('event_list'))
if unapproved_event.name not in response.content.decode():
    print("✅ Unapproved event not in public list - CORRECT")
else:
    print("❌ Unapproved event visible in public list - SECURITY ISSUE!")

# Clean up
unapproved_event.delete()
staff_user.delete()

print("\n✅ Testing complete!")