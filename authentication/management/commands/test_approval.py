# event_management/management/commands/test_approval.py

from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from event_management.models import Event
from django.urls import reverse

User = get_user_model()


class Command(BaseCommand):
    help = 'Test event approval system security'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting event approval tests...\n")

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

        # Get or create unapproved event
        unapproved_event = Event.objects.filter(is_approved=False).first()
        if not unapproved_event:
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
            self.stdout.write(self.style.SUCCESS(f"✅ Created test event: {unapproved_event.slug}"))

        # Run tests
        self.test_anonymous_access(anonymous_client, unapproved_event)
        self.test_staff_access(staff_client, unapproved_event)
        self.test_event_list(anonymous_client, unapproved_event)
        
        # Cleanup
        if 'test-unapproved-event' in unapproved_event.slug:
            unapproved_event.delete()
        staff_user.delete()
        
        self.stdout.write(self.style.SUCCESS("\n✅ Testing complete!"))

    def test_anonymous_access(self, client, event):
        self.stdout.write("\n🔍 Testing anonymous access to unapproved event...")
        response = client.get(reverse('event_detail', kwargs={'slug': event.slug}))
        
        if response.status_code == 404:
            self.stdout.write(self.style.SUCCESS("✅ Anonymous user gets 404 - CORRECT"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ SECURITY ISSUE: Got {response.status_code}"))

    def test_staff_access(self, client, event):
        self.stdout.write("\n🔍 Testing staff access to unapproved event...")
        response = client.get(reverse('event_detail', kwargs={'slug': event.slug}))
        
        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS("✅ Staff can access - CORRECT"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Staff got {response.status_code}"))

    def test_event_list(self, client, event):
        self.stdout.write("\n🔍 Testing public event list...")
        response = client.get(reverse('event_list'))
        
        if event.name not in response.content.decode():
            self.stdout.write(self.style.SUCCESS("✅ Unapproved event hidden - CORRECT"))
        else:
            self.stdout.write(self.style.ERROR("❌ Unapproved event visible!"))