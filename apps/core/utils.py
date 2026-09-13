"""Utility functions for booking chat operations."""
from django.utils import timezone
from apps.core.models import ChatMessage, Notification
from apps.core.notification_service import create_and_send_notification


def create_chat_message(booking, sender, message_text):
    """
    Create a new chat message for a booking.
    
    Args:
        booking: Booking instance
        sender: User object (who is sending the message)
        message_text: The message content
        
    Returns:
        ChatMessage instance
    """
    message = ChatMessage.objects.create(
        booking=booking,
        sender=sender,
        message=message_text
    )
    return message


def notify_message_recipient(booking, sender, message):
    """
    Send notification to the other party (recipient) if they're not in the chat.
    Supports multiple channels: in_app, email, SMS
    
    Args:
        booking: Booking instance
        sender: User who sent the message
        message: ChatMessage instance
    """
    recipient = message.get_recipient()
    
    # Check if recipient is actively in the chat (using cache)
    from django.core.cache import cache
    recipient_cache_key = f"active_chat_user_{recipient.id}"
    recipient_active_chat = cache.get(recipient_cache_key)
    
    # Only notify if they're NOT in this specific booking's chat
    if recipient_active_chat != booking.id:
        # Determine message title
        sender_name = sender.get_full_name() or sender.username
        title = f"New Message from {sender_name}"
        
        # Prepare message preview
        message_preview = message.message[:80]
        if len(message.message) > 80:
            message_preview += "..."
        
        # Create notification link
        notification_link = f"/dashboard/booking/{booking.booking_id}/chat/"
        
        # Send in-app notification (always)
        create_and_send_notification(
            user=recipient,
            title=title,
            message=message_preview,
            channel='in_app',
            link=notification_link
        )
        
        # Send email notification if user has email
        if recipient.email:
            email_subject = f"New message from {sender_name} - {booking.booking_id}"
            email_message = f"""
            Hello {recipient.get_full_name() or recipient.username},
            
            You have a new message from {sender_name} regarding booking {booking.booking_id}:
            
            "{message.message}"
            
            Reply to this message on PurohitConnect:
            {notification_link}
            
            Best regards,
            PurohitConnect Team
            """
            
            create_and_send_notification(
                user=recipient,
                title=email_subject,
                message=email_message,
                channel='email',
                link=notification_link
            )


def mark_booking_chat_as_read(booking, user):
    """
    Mark all unread messages in a booking chat as read for a user.
    
    Args:
        booking: Booking instance
        user: User who is reading the messages
        
    Returns:
        int: Number of messages marked as read
    """
    count = ChatMessage.mark_booking_messages_as_read(booking, user)
    return count


def get_booking_chat_messages(booking):
    """
    Get all messages for a booking, ordered by creation date.
    
    Args:
        booking: Booking instance
        
    Returns:
        QuerySet of ChatMessage objects
    """
    return booking.messages.all()


def get_chat_context(booking, user):
    """
    Get complete chat context for rendering in template.
    
    Args:
        booking: Booking instance
        user: Current user
        
    Returns:
        dict: Chat context with messages, participants, and metadata
    """
    messages = booking.messages.all()
    unread_count = messages.filter(is_read=False).exclude(sender=user).count()
    
    # Mark all as read
    mark_booking_chat_as_read(booking, user)
    
    # Determine participants and roles
    is_customer = user == booking.customer
    is_purohit = hasattr(user, 'purohit_profile') and user.purohit_profile.purohit_listing == booking.purohit
    
    return {
        'messages': messages,
        'unread_count': unread_count,
        'is_customer': is_customer,
        'is_purohit': is_purohit,
        'customer': booking.customer,
        'purohit': booking.purohit.profile.user,
        'booking': booking,
    }
