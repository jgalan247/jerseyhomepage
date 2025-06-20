# event_management/management/commands/test_email.py
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from authentication.models import User

class Command(BaseCommand):
    help = 'Test email functionality'

    def handle(self, *args, **options):
        # Test 1: Basic email
        self.stdout.write('Testing basic email...')
        try:
            send_mail(
                'Test Email from Jersey Events',
                'This is a test email. If you see this, email is working!',
                'noreply@jerseyevents.com',
                ['test@example.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('✓ Basic email sent!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Basic email failed: {e}'))
        
        # Test 2: HTML email
        self.stdout.write('\nTesting HTML email...')
        try:
            html_message = """
            <html>
                <body>
                    <h2>Jersey Events Test Email</h2>
                    <p>This is a <strong>HTML email</strong> test.</p>
                    <p>If you can see this with formatting, HTML emails work!</p>
                </body>
            </html>
            """
            send_mail(
                'Test HTML Email',
                'This is the plain text version.',
                'noreply@jerseyevents.com',
                ['test@example.com'],
                fail_silently=False,
                html_message=html_message
            )
            self.stdout.write(self.style.SUCCESS('✓ HTML email sent!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ HTML email failed: {e}'))
        
        # Test 3: User verification email (simulate)
        self.stdout.write('\nTesting user verification email...')
        user = User.objects.first()
        if user:
            try:
                # Simulate verification email
                verification_url = f"http://localhost:8000/auth/verify-email/{user.email_verification_token}/"
                
                message = f"""
                Welcome to Jersey Events!
                
                Please verify your email by clicking the link below:
                {verification_url}
                
                Your verification token: {user.email_verification_token}
                
                Best regards,
                Jersey Events Team
                """
                
                send_mail(
                    'Verify your Jersey Events account',
                    message,
                    'noreply@jerseyevents.com',
                    [user.email],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Verification email sent to {user.email}!'))
                self.stdout.write(f'  Token: {user.email_verification_token}')
                self.stdout.write(f'  URL: {verification_url}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Verification email failed: {e}'))
        else:
            self.stdout.write(self.style.WARNING('No users found. Create a user first.'))
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Email configuration:')
        from django.conf import settings
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        if hasattr(settings, 'EMAIL_HOST'):
            self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
            self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')