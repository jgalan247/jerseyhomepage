from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import get_connection, EmailMessage
import socket


class Command(BaseCommand):
    help = 'Debug Django email configuration and test MailHog connection'

    def handle(self, *args, **options):
        self.stdout.write("Current Email Configuration:")
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        self.stdout.write(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        self.stdout.write(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
        self.stdout.write(f"EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', 'Not set')}")
        
        # Check if using console backend
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            self.stdout.write(self.style.WARNING(
                "\n⚠️  You're using console backend! Emails are printed to console, not sent to MailHog."
            ))
            self.stdout.write("\nAdd this to your settings.py:")
            self.stdout.write("""
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'  # or 'mailhog' if in Docker
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
            """)
        
        # Test connection
        self.stdout.write("\nTesting MailHog connectivity:")
        self.test_connection('localhost', 1025)
        self.test_connection('mailhog', 1025)
        
        # Send test email
        self.send_test_email()
    
    def test_connection(self, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                self.stdout.write(self.style.SUCCESS(f"✅ Can connect to {host}:{port}"))
                return True
            else:
                self.stdout.write(self.style.ERROR(f"❌ Cannot connect to {host}:{port}"))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Connection error: {e}"))
            return False
    
    def send_test_email(self):
        self.stdout.write("\nSending test email with explicit SMTP backend...")
        try:
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host='localhost',  # Change to 'mailhog' if in Docker
                port=1025,
                use_tls=False,
                use_ssl=False,
                fail_silently=False
            )
            
            email = EmailMessage(
                'Test from Django Debug Command',
                'This should appear in MailHog',
                'test@example.com',
                ['recipient@example.com'],
                connection=connection
            )
            
            result = email.send()
            self.stdout.write(self.style.SUCCESS(f"Email sent: {result}"))
            self.stdout.write("Check MailHog at http://localhost:8025")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error sending email: {e}"))
            self.stdout.write("\nPossible solutions:")
            self.stdout.write("1. If using Docker, make sure both containers are on the same network")
            self.stdout.write("2. Try using 'mailhog' instead of 'localhost' as EMAIL_HOST")
            self.stdout.write("3. Check if MailHog container is running: docker ps")
