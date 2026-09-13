"""Email service for sending notifications via Django's email backend or SendGrid."""
import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending notifications and transactional emails."""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@purohitconnect.com')
        self.is_configured = bool(getattr(settings, 'EMAIL_HOST', None))
    
    def send_notification_email(self, user, title, message, link=None, is_html=False):
        """
        Send notification email to user.
        
        Args:
            user: CustomUser instance
            title: Email subject/title
            message: Email body content
            link: Optional link to include in email
            is_html: Whether message contains HTML
        
        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
        if not user.email:
            logger.warning(f"User {user.username} has no email address")
            return False, None, "No email address on file"
        
        if not self.is_configured:
            logger.warning("Email service not configured, using mock")
            return self._mock_send_email(user, title, message)
        
        try:
            subject = title
            text_content = message
            html_content = message if is_html else None
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[user.email]
            )
            
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            result = email.send()
            
            if result:
                message_id = getattr(email, 'message_id', None)
                logger.info(f"Email sent successfully to {user.email}: {subject}")
                return True, message_id, None
            else:
                logger.error(f"Failed to send email to {user.email}")
                return False, None, "Email backend returned False"
                
        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {str(e)}")
            return False, None, str(e)
    
    def send_otp_email(self, user, otp_code):
        """
        Send OTP verification email.
        
        Args:
            user: CustomUser instance
            otp_code: OTP code to send
        
        Returns:
            tuple: (success: bool, message_id: str or None, error: str or None)
        """
        subject = "Your PurohitConnect Verification Code"
        message = f"""
        Hello {user.get_full_name() or user.username},
        
        Your PurohitConnect verification code is: {otp_code}
        
        This code will expire in 5 minutes. If you didn't request this, please ignore this email.
        
        Best regards,
        PurohitConnect Team
        """
        
        return self.send_notification_email(user, subject, message)
    
    def send_booking_confirmation_email(self, booking):
        """
        Send booking confirmation email to customer and purohit.
        
        Args:
            booking: Booking instance
        
        Returns:
            dict: {'customer': (success, msg_id, error), 'purohit': (success, msg_id, error)}
        """
        customer_msg = f"""
        Hello {booking.customer.get_full_name() or booking.customer.username},
        
        Your booking for {booking.puja_package.puja.name} has been confirmed!
        
        Booking ID: {booking.booking_id}
        Purohit: {booking.purohit.name}
        Date: {booking.scheduled_date}
        Location: {booking.location}
        Amount: ₹{booking.total_amount}
        
        You will receive your start verification code on the day of the ritual.
        
        Best regards,
        PurohitConnect Team
        """
        
        purohit_msg = f"""
        Hello {booking.purohit.name},
        
        You have a new booking!
        
        Booking ID: {booking.booking_id}
        Customer: {booking.customer.get_full_name() or booking.customer.username}
        Puja: {booking.puja_package.puja.name}
        Date: {booking.scheduled_date}
        Location: {booking.location}
        
        Please confirm if you can accept this booking.
        
        Best regards,
        PurohitConnect Team
        """
        
        results = {
            'customer': self.send_notification_email(
                booking.customer,
                "Booking Confirmed",
                customer_msg
            ),
            'purohit': self.send_notification_email(
                booking.purohit.profile.user,
                "New Booking",
                purohit_msg
            )
        }
        
        return results
    
    def _mock_send_email(self, user, subject, message):
        """Mock email sending for development/testing."""
        logger.info(f"MOCK EMAIL to {user.email}: {subject}")
        print(f"📧 MOCK EMAIL to {user.email}:")
        print(f"   Subject: {subject}")
        print(f"   Body: {message[:100]}...")
        return True, "mock_message_id", None


# Global email service instance
email_service = EmailService()


def send_email(user, subject, message, is_html=False):
    """
    Convenience function to send email notification.
    
    Args:
        user: CustomUser instance
        subject: Email subject
        message: Email body
        is_html: Whether message is HTML
    
    Returns:
        tuple: (success: bool, message_id: str or None, error: str or None)
    """
    return email_service.send_notification_email(user, subject, message, is_html=is_html)
