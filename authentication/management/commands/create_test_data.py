from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Organizer

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test data for ticket booking system'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')

        # Create test customer - VERIFIED
        user, created = User.objects.get_or_create(
            username='testbuyer',
            defaults={
                'email': 'buyer@test.com',
                'first_name': 'John',
                'last_name': 'Customer',
                'is_email_verified': True,  # ✅ Mark as verified
                'is_active': True,
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        else:
            # Update existing user to be verified
            user.is_email_verified = True
            user.is_active = True
            user.save()
        self.stdout.write(f"✅ Customer: {user.username} (verified)")

        # Create organizer user - VERIFIED
        organizer_user, created = User.objects.get_or_create(
            username='testorganizer',
            defaults={
                'email': 'organizer@test.com',
                'first_name': 'Jane',
                'last_name': 'Organizer',
                'is_email_verified': True,  # ✅ Mark as verified
                'is_active': True,
            }
        )
        if created:
            organizer_user.set_password('testpass123')
            organizer_user.save()
        else:
            # Update existing user to be verified
            organizer_user.is_email_verified = True
            organizer_user.is_active = True
            organizer_user.save()

        # Create organizer profile
        organizer, created = Organizer.objects.get_or_create(
            user=organizer_user,
            defaults={
                'company_name': 'Test Events Ltd',
                'business_email': 'organizer@test.com',
                'is_verified': True,
            }
        )
        self.stdout.write(f"✅ Organizer: {organizer.company_name} (verified)")

        self.stdout.write('\n🎉 Test data created!')
        self.stdout.write('✅ Customer: testbuyer / testpass123 (EMAIL VERIFIED)')
        self.stdout.write('✅ Organizer: testorganizer / testpass123 (EMAIL VERIFIED)')
        self.stdout.write('Visit: http://localhost:8000')
