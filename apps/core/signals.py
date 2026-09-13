"""Signal handlers for core app models."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from apps.core.models import Notification
from apps.core.notification_service import delivery_service
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def send_notification_on_create(sender, instance, created, **kwargs):
    """
    Send notification immediately after creation if not in_app.
    For in_app notifications, mark as delivered immediately.
    """
    if created:
        # For in_app notifications, mark as delivered immediately
        if instance.channel == 'in_app':
            instance.delivery_status = 'delivered'
            instance.save(update_fields=['delivery_status'])
            logger.info(f"In-app notification {instance.id} marked as delivered")
        else:
            # For other channels, send asynchronously
            # In production, use Celery or similar for async tasks
            try:
                success, reference, error = delivery_service.send_notification(instance)
                logger.info(f"Sent notification {instance.id} via {instance.channel}: {success}")
            except Exception as e:
                logger.error(f"Error sending notification {instance.id}: {str(e)}")
