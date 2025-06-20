from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.views import send_verification_email
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Send a test verification email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send to',
            default='test@example.com'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f'Sending verification email to: {email}\n')
        
        # Try to get existing user or create new one
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f'Found existing user: {user.username}')
            
            # Reset their verification status for testing
            user.email_verified = False
            user.is_active = False
            user.email_verification_token = uuid.uuid4()  # Generate new token
            user.save()
            self.stdout.write(f'Reset user verification status')
            
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0] + '_' + uuid.uuid4().hex[:6]
            user = User.objects.create_user(
                username=username,
                email=email,
                password='testpass123',
                first_name='Test',
                last_name='User',
                is_active=False,
                email_verified=False
            )
            self.stdout.write(f'Created new user: {username}')
        
        # Send verification email
        try:
            send_verification_email(user)
            self.stdout.write(self.style.SUCCESS('\n✅ Verification email sent!'))
            self.stdout.write(f'\nUser details:')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Token: {user.email_verification_token}')
            self.stdout.write(f'  Verification URL: http://localhost:8000/auth/verify-email/{user.email_verification_token}/')
            self.stdout.write(f'\nCheck your email or console output above!')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Failed to send email: {e}'))