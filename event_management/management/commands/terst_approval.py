# event_management/management/commands/test_approval.py

from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from event_management.models import Event

User = get_user_model()


class Command(BaseCommand):
    help = 'Test event approval system'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Testing event approval system...\n')
        
        # Create anonymous client
        client = Client()
        
        # Find or create unapproved event
        event = Event.objects.filter(is_approved=False).first()
        if not event:
            event = Event.objects.create(
                name="Test Unapproved Event",
                slug="test-unapproved-event",
                description="Test",
                location="St Helier",
                date="2025-07-01",
                time="19:00",
                price=10.00,
                is_approved=False
            )
            self.stdout.write(f'Created test event: {event.slug}')
        
        # Test anonymous access
        response = client.get(f'/events/{event.slug}/')
        if response.status_code == 404:
            self.stdout.write(self.style.SUCCESS('✅ Anonymous gets 404 - GOOD'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Anonymous got {response.status_code}'))
        
        # Test list view
        response = client.get('/events/')
        if event.name not in response.content.decode():
            self.stdout.write(self.style.SUCCESS('✅ Hidden from list - GOOD'))
        else:
            self.stdout.write(self.style.ERROR('❌ Visible in list - BAD'))
        
        # Clean up
        if 'test-unapproved' in event.slug:
            event.delete()
            
        self.stdout.write(self.style.SUCCESS('\n✅ Test complete!'))