"""
Django settings for jersey_homepage project.
"""

from pathlib import Path
import dj_database_url
from decouple import config, Csv
import environ
import os

# Initialize environ
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)


# Read .env file
environ.Env.read_env()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-this')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

BASE_URL = config('BASE_URL', default='http://localhost:8000')

CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000', cast=Csv())
# CSRF TRUSTED ORIGINS - Required for Django 4.0+
#CSRF_TRUSTED_ORIGINS = [
#    'http://localhost:8000',
#    'http://127.0.0.1:8000',
#    'http://0.0.0.0:8000',
#]

# CSRF settings for development
if DEBUG:
    CSRF_COOKIE_SECURE = False
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_SAMESITE = 'Lax'
    # Session cookie settings for development
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Add this
    #'authentication',  # Your existing auth app
    #'event_management',
    #'booking', 
    'django_htmx',
    #'payments',
    'widget_tweaks',
    # Our apps
    # 'events',
    'authentication.apps.AuthenticationConfig',  # Make sure this includes .apps.AuthenticationConfig
    'event_management.apps.EventManagementConfig',  # Make sure this includes .apps.EventManagementConfig
    'booking.apps.BookingConfig',  # Add this if you don't have it
    'payments.apps.PaymentsConfig',  # Add this if you don't have it
    
    # Third party apps (we'll add these as needed)
    # 'django_htmx',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

# Add debug toolbar in development
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

ROOT_URLCONF = 'jersey_homepage.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'booking.views.cart_context',  # Cart context processor - NOW ACTIVE
            ],
        },
    },
]

WSGI_APPLICATION = 'jersey_homepage.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.parse(
        #config('DATABASE_URL', default='postgres://jersey_user:jersey_secure_pass_123@db:5432/jersey_roothp')
        config('DATABASE_URL', default='postgres://jersey_user:jersey_secure_pass_123@localhost:5432/jersey_homepage')
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# Login/Logout URLs
LOGIN_URL = 'authentication:login'
LOGIN_REDIRECT_URL = 'event_management:event_list'
LOGOUT_REDIRECT_URL = 'event_management:event_list'

# Site configuration
SITE_NAME = config('SITE_NAME', default='Jersey Homepage')
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Email configuration (for sending tickets)
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
#EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
#EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
#EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
#EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
#DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=f'{SITE_NAME} <noreply@jerseyevents.com>')
# For Django (settings.py)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mailhog' # 'localhost'  if not using Docker networking
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'noreply@jerseyhomepage.com'
# Messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# ===== NEW BOOKING SYSTEM SETTINGS =====


# PayPal Commerce Platform
PAYPAL_MODE = env('PAYPAL_MODE', default='sandbox')  # Removed duplicate config() line
PAYPAL_CLIENT_ID = env('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = env('PAYPAL_CLIENT_SECRET')
PAYPAL_PARTNER_ID = env('PAYPAL_PARTNER_ID')  # Your BN Code
PAYPAL_BRAND_NAME = env('PAYPAL_BRAND_NAME', default='Jersey Events')  # NEW: Added brand name

# Use sandbox for development, live for production
if PAYPAL_MODE == 'sandbox':  # Changed from DEBUG to use PAYPAL_MODE
    PAYPAL_BASE_URL = 'https://api-m.sandbox.paypal.com'
    #PAYPAL_WEBHOOK_ID = env('PAYPAL_SANDBOX_WEBHOOK_ID', default='')
else:
    PAYPAL_BASE_URL = 'https://api-m.paypal.com'
    #PAYPAL_WEBHOOK_ID = env('PAYPAL_LIVE_WEBHOOK_ID', default='')
    # Override with live credentials if available
    PAYPAL_CLIENT_ID = env('PAYPAL_LIVE_CLIENT_ID', default=PAYPAL_CLIENT_ID)
    PAYPAL_CLIENT_SECRET = env('PAYPAL_LIVE_CLIENT_SECRET', default=PAYPAL_CLIENT_SECRET)


PAYPAL_WEBHOOK_ID = 'WH1234567890ABCDEF'
# Platform settings
PLATFORM_FEE_PERCENTAGE = env('PLATFORM_FEE_PERCENTAGE', default=5.0)
SITE_URL = env('SITE_URL', default='http://localhost:8000')

# Optional: Add site domain for emails (if different from SITE_URL)
SITE_DOMAIN = env('SITE_DOMAIN', default=SITE_URL)

# Optional: Skip webhook verification in development (NEVER use in production)
SKIP_WEBHOOK_VERIFICATION = env('SKIP_WEBHOOK_VERIFICATION', default=False, cast=bool) and DEBUG


# How to get these values:
"""
1. PAYPAL_CLIENT_ID & PAYPAL_CLIENT_SECRET:
   - Log in to https://developer.paypal.com
   - Go to Dashboard > My Apps & Credentials
   - Create a new app (or use existing)
   - You'll get both Sandbox and Live credentials

2. PAYPAL_PARTNER_ID (BN Code):
   - Apply for PayPal Partner program
   - You'll receive a Partner ID (BN Code)
   - This identifies your platform in transactions

3. PAYPAL_WEBHOOK_ID:
   - In PayPal Developer Dashboard
   - Go to your app > Webhooks
   - Create webhook for your endpoints
   - Subscribe to these events:
     * MERCHANT.ONBOARDING.COMPLETED
     * MERCHANT.PARTNER-CONSENT.REVOKED
     * PAYMENT.CAPTURE.COMPLETED
     * PAYMENT.CAPTURE.REFUNDED

4. Testing in Sandbox:
   - Create test business accounts at https://developer.paypal.com/dashboard/accounts
   - Use these for testing organizer onboarding
   - Create test buyer accounts for payment testing
"""


# Session configuration for cart
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400 * 7  # 7 days - cart persists for a week
SESSION_SAVE_EVERY_REQUEST = True  # Update session on every request to keep cart alive

# Celery Configuration (optional - for async email sending)
# Uncomment these if you want to use Celery for background tasks
# CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
# CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = TIME_ZONE

# Security settings for payment processing
if not DEBUG:
    # Force HTTPS in production
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Use SMTP even in DEBUG
    EMAIL_HOST = 'mailhog' # if Django is in Docker
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False
else:
    # Production email settings
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')

#CSRF_TRUSTED_ORIGINS = [
#    'http://localhost:8000',
#    'http://127.0.0.1:8000',
#    'http://0.0.0.0:8000',
#]

# Tier 1: Orders up to £500 - 8% fee
PLATFORM_FEE_TIER_1_MAX = env('PLATFORM_FEE_TIER_1_MAX', default=500)
PLATFORM_FEE_TIER_1_RATE = env('PLATFORM_FEE_TIER_1_RATE', default=0.08)

# Tier 2: Orders £501-£2000 - 6% fee  
PLATFORM_FEE_TIER_2_MAX = env('PLATFORM_FEE_TIER_2_MAX', default=2000)
PLATFORM_FEE_TIER_2_RATE = env('PLATFORM_FEE_TIER_2_RATE', default=0.06)

# Tier 3: Orders £2001-£5000 - 4% fee
PLATFORM_FEE_TIER_3_MAX = env('PLATFORM_FEE_TIER_3_MAX', default=5000)
PLATFORM_FEE_TIER_3_RATE = env('PLATFORM_FEE_TIER_3_RATE', default=0.04)

# Tier 4: Orders over £5000 - 3% fee
PLATFORM_FEE_TIER_4_RATE = env('PLATFORM_FEE_TIER_4_RATE', default=0.03)

# Optional: Minimum fee regardless of percentage
PLATFORM_FEE_MINIMUM = env('PLATFORM_FEE_MINIMUM', default=0.50)  # 50p minimum

# Brand and platform names
TICKET_BRAND_NAME = os.getenv('TICKET_BRAND_NAME', 'JERSEY EVENTS')
TICKET_PLATFORM_NAME = os.getenv('TICKET_PLATFORM_NAME', 'Jersey Homepage - Your Local Event Platform')

# PDF titles and headings
TICKET_CONFIRMATION_TITLE = os.getenv('TICKET_CONFIRMATION_TITLE', 'Order Confirmation')
TICKET_SUMMARY_TITLE = os.getenv('TICKET_SUMMARY_TITLE', 'Tickets Included')
TICKET_SINGLE_TITLE = os.getenv('TICKET_SINGLE_TITLE', 'Event Ticket')

# Ticket instructions and text
TICKET_QR_SCAN_TEXT = os.getenv('TICKET_QR_SCAN_TEXT', 'Scan at entrance')
TICKET_VENUE_INSTRUCTION = os.getenv('TICKET_VENUE_INSTRUCTION', 'Present this ticket at the venue entrance.')
TICKET_VALIDITY_TEXT = os.getenv('TICKET_VALIDITY_TEXT', 'This ticket is valid for one admission only.')

# Footer disclaimer (supports multiline with \n)
TICKET_FOOTER_DISCLAIMER = os.getenv('TICKET_FOOTER_DISCLAIMER', 
    'This ticket is valid for one admission only. Duplication is prohibited.\n'
    'Please have this ticket ready for scanning at the venue entrance.'
)

# Important notice section (HTML formatted)
TICKET_IMPORTANT_NOTICE = os.getenv('TICKET_IMPORTANT_NOTICE', """
<b>Important Information:</b><br/>
- Each ticket has a unique QR code - do not share or duplicate<br/>
- Present tickets on your phone or printed at the venue<br/>
- Doors open 30 minutes before event start time<br/>
- Keep this PDF safe - it contains all your tickets
""")

# PayPal Webhook Configuration
# PAYPAL_WEBHOOK_ID = os.getenv('PAYPAL_WEBHOOK_ID', '')

# Optional: Skip verification in development (NEVER use in production)
SKIP_WEBHOOK_VERIFICATION = os.getenv('SKIP_WEBHOOK_VERIFICATION', 'False').lower() == 'true' and DEBUG

# Admin notification emails
ADMIN_NOTIFICATION_EMAILS = [
    'admin@coderra.je',  # Your admin email
    # Add more admin emails as needed
]

# Alternative: use the existing ADMINS setting
ADMINS = [
    ('Jersey Homepage Admin', 'admin@coderra.je'),
]
ADMIN_NOTIFICATION_EMAILS = ['admin@coderra.je']
# Make sure these email settings are configured
# (You probably already have these, but double-check)
DEFAULT_FROM_EMAIL = 'Jersey Homepage <noreply@jerseyhomepage.com>'

# If using Gmail/SMTP (example configuration)
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
#EMAIL_USE_TLS = True
#EMAIL_HOST_USER = 'your-email@gmail.com'
#EMAIL_HOST_PASSWORD = 'your-app-password'  # Use app-specific password for Gmail

# For development, you can use console backend to see emails in console
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging configuration to track email sending
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'admin_notifications.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'authentication.utils': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'authentication.signals': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'event_management.signals': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
