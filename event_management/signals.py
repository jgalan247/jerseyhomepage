from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event
from authentication.utils import send_admin_event_notification
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Event)
def notify_admin_new_event(sender, instance, created, **kwargs):
    """Send admin notification when new event is created"""
    if created and not instance.is_active:  # Assuming events need approval to be active
        logger.info(f"New event created: {instance.title}, sending admin notification")
        send_admin_event_notification(instance)
