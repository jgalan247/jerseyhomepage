from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Organizer
from .utils import send_admin_organizer_notification
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Organizer)
def notify_admin_new_organizer(sender, instance, created, **kwargs):
    """Send admin notification when new organizer registers"""
    if created and not instance.is_verified:
        logger.info(f"New organizer created: {instance.company_name}, sending admin notification")
        send_admin_organizer_notification(instance)
