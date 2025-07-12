from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

def send_admin_organizer_notification(organizer):
    """Send email notification to admins when new organizer registers"""
    try:
        # Get admin emails from settings
        admin_emails = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', [])
        if not admin_emails:
            # Fallback to ADMINS setting
            admin_emails = [email for name, email in getattr(settings, 'ADMINS', [])]
        
        if not admin_emails:
            logger.warning("No admin emails configured for organizer notifications")
            return False

        # Build admin URL for organizer approval
        admin_url = f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/admin/authentication/organizer/{organizer.id}/change/"
        
        # Render email template
        context = {
            'organizer': organizer,
            'admin_url': admin_url,
            'site_name': 'Jersey Homepage',
            'site_url': getattr(settings, 'BASE_URL', 'http://localhost:8000')
        }
        
        # Use your existing template structure
        html_message = render_to_string('authentication/emails/admin_new_organizer.html', context)
        plain_message = render_to_string('authentication/emails/admin_new_organizer.txt', context)
        
        # Send email
        send_mail(
            subject=f'🏢 New Organizer Registration: {organizer.company_name}',
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jerseyhomepage.com'),
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Admin notification sent for new organizer: {organizer.company_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin organizer notification: {str(e)}")
        return False


def send_admin_event_notification(event):
    """Send email notification to admins when new event is created"""
    try:
        # Get admin emails from settings
        admin_emails = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', [])
        if not admin_emails:
            # Fallback to ADMINS setting
            admin_emails = [email for name, email in getattr(settings, 'ADMINS', [])]
        
        if not admin_emails:
            logger.warning("No admin emails configured for event notifications")
            return False

        # Build URLs
        admin_url = f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/admin/event_management/event/{event.id}/change/"
        
        # Nested try block for event URL generation
        try:
            if hasattr(event, 'slug') and event.slug:
                event_url = f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/events/{event.slug}/"
            else:
                # Fallback to admin URL if no slug
                event_url = f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/admin/event_management/event/{event.id}/change/"
        except Exception as url_error:
            # Ultimate fallback for URL generation
            logger.warning(f"URL generation failed: {url_error}")
            event_url = f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/events/"
        
        # Render email template
        context = {
            'event': event,
            'admin_url': admin_url,
            'event_url': event_url,
            'site_name': 'Jersey Homepage',
            'site_url': getattr(settings, 'BASE_URL', 'http://localhost:8000')
        }
        
        # Use your template structure
        html_message = render_to_string('event_management/emails/admin_new_event.html', context)
        plain_message = render_to_string('event_management/emails/admin_new_event.txt', context)
        
        # Send email
        send_mail(
            subject=f'📅 New Event Pending Approval: {event.title}',
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@jerseyhomepage.com'),
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Admin notification sent for new event: {event.title}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin event notification: {str(e)}")
        return False
