"""Unified notification delivery service for all channels."""
import logging
from django.utils import timezone
from apps.core.models import Notification
from apps.core.email_service import email_service
from apps.accounts.utils import sms_service

logger = logging.getLogger(__name__)


class NotificationDeliveryService:
    """Handles delivery of notifications across multiple channels."""
    
    def __init__(self):
        self.email_service = email_service
        self.sms_service = sms_service
    
    def send_notification(self, notification):
        """
        Send a single notification through its configured channel.
        
        Args:
            notification: Notification instance
        
        Returns:
            tuple: (success: bool, reference: str, error: str)
        """
        if notification.channel == 'email':
            return self._send_email_notification(notification)
        elif notification.channel == 'sms':
            return self._send_sms_notification(notification)
        elif notification.channel == 'in_app':
            return self._send_in_app_notification(notification)
        elif notification.channel == 'whatsapp':
            return self._send_whatsapp_notification(notification)
        else:
            return False, None, f"Unknown channel: {notification.channel}"
    
    def send_pending_notifications(self, limit=100):
        """
        Send all pending notifications.
        
        Args:
            limit: Maximum number of notifications to send
        
        Returns:
            dict: {'sent': int, 'failed': int, 'errors': list}
        """
        pending = Notification.objects.filter(
            delivery_status='pending'
        ).order_by('created_at')[:limit]
        
        results = {'sent': 0, 'failed': 0, 'errors': []}
        
        for notification in pending:
            success, reference, error = self.send_notification(notification)
            
            if success:
                notification.delivery_status = 'sent'
                notification.delivery_reference = reference or ''
                notification.sent_at = timezone.now()
                notification.save()
                results['sent'] += 1
                logger.info(f"Sent notification {notification.id} via {notification.channel}")
            else:
                notification.delivery_status = 'failed'
                notification.delivery_error = error or 'Unknown error'
                notification.save()
                results['failed'] += 1
                results['errors'].append({
                    'notification_id': notification.id,
                    'error': error
                })
                logger.error(f"Failed to send notification {notification.id}: {error}")
        
        return results
    
    def _send_email_notification(self, notification):
        """Send notification via email."""
        try:
            success, msg_id, error = self.email_service.send_notification_email(
                notification.user,
                notification.title,
                notification.message,
                link=notification.link
            )
            
            return success, msg_id, error
            
        except Exception as e:
            logger.error(f"Error sending email notification {notification.id}: {str(e)}")
            return False, None, str(e)
    
    def _send_sms_notification(self, notification):
        """Send notification via SMS."""
        try:
            if not notification.user.phone:
                return False, None, "User has no phone number"

            body = f"{notification.title}: {notification.message}"
            if notification.link:
                body = f"{body}\n{notification.link}"

            success, message, sid = self.sms_service.send_sms(
                notification.user.phone,
                body[:1600]
            )

            return success, sid, None if success else message

        except Exception as e:
            logger.error(f"Error sending SMS notification {notification.id}: {str(e)}")
            return False, None, str(e)

    def _send_in_app_notification(self, notification):
        """Mark in-app notification as sent (already in DB)."""
        notification.delivery_status = 'delivered'
        notification.delivered_at = timezone.now()
        notification.save()
        return True, None, None

    def _send_whatsapp_notification(self, notification):
        """Send notification via Twilio WhatsApp API."""
        try:
            if not notification.user.phone:
                return False, None, "User has no phone number"

            body = f"*{notification.title}*\n{notification.message}"
            if notification.link:
                body = f"{body}\n{notification.link}"

            success, message, sid = self.sms_service.send_whatsapp(
                notification.user.phone,
                body[:1600]
            )
            return success, sid, None if success else message
        except Exception as e:
            logger.error(f"Error sending WhatsApp notification {notification.id}: {str(e)}")
            return False, None, str(e)
    
    def mark_as_read(self, notification):
        """
        Mark notification as read by user.
        
        Args:
            notification: Notification instance
        """
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()


# Global delivery service instance
delivery_service = NotificationDeliveryService()


def send_notification(notification):
    """
    Convenience function to send a notification.
    
    Args:
        notification: Notification instance
    
    Returns:
        tuple: (success: bool, reference: str, error: str)
    """
    return delivery_service.send_notification(notification)


def create_and_send_notification(user, title, message, channel='in_app', link=None):
    """
    Create a notification and send it immediately.
    
    Args:
        user: CustomUser instance
        title: Notification title
        message: Notification message
        channel: Delivery channel ('in_app', 'email', 'sms', 'whatsapp')
        link: Optional link for the notification
    
    Returns:
        tuple: (notification, success, reference, error)
    """
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        channel=channel,
        link=link
    )
    
    # For in_app, mark as delivered immediately
    if channel == 'in_app':
        success, reference, error = delivery_service.send_notification(notification)
    else:
        # For other channels, send asynchronously
        success, reference, error = delivery_service.send_notification(notification)
    
    return notification, success, reference, error
