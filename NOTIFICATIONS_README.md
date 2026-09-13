# Email/SMS Notification Delivery System

## Overview

PurohitConnect now features a comprehensive multi-channel notification delivery system that supports:

- **In-App Notifications** - Displayed in the dashboard
- **Email Notifications** - Sent via SMTP or console (dev)
- **SMS Notifications** - Sent via Twilio
- **WhatsApp** - Ready for WhatsApp Business API integration

## Features

### 1. Notification Model Enhancements
The `Notification` model now tracks:
- **Channel**: Where to send (in_app, email, sms, whatsapp)
- **Delivery Status**: pending, sent, delivered, failed, bounced
- **Delivery Reference**: ID from email/SMS provider for tracking
- **Delivery Error**: Error details if delivery fails
- **Timestamps**: sent_at, delivered_at, read_at for audit trail

### 2. Services

#### Email Service (`apps/core/email_service.py`)
- Sends notifications via Django email backend
- Mock mode for development (console output)
- Supports HTML and plain text emails
- Special methods for OTP, booking confirmations

```python
from apps.core.email_service import send_email

send_email(user, subject="Welcome", message="Hello!")
```

#### Notification Delivery Service (`apps/core/notification_service.py`)
- Unified interface for all notification channels
- Automatic signal-based delivery on creation
- Batch delivery support via management command
- Delivery status tracking and error handling

```python
from apps.core.notification_service import create_and_send_notification

# Create and send immediately
notification, success, ref, error = create_and_send_notification(
    user=user,
    title="New Message",
    message="You have a new message",
    channel='email',
    link='/chat/'
)
```

### 3. Management Commands

#### Send Pending Notifications
```bash
python manage.py send_notifications --limit=100
```

Options:
- `--limit`: Max notifications to send (default: 100)
- `--channel`: Filter by channel (email, sms, in_app, whatsapp)

#### Cleanup Expired OTPs
```bash
python manage.py cleanup_otp --dry-run
```

## Configuration

### Email Configuration

**Development (Console Output)**
```python
# config/settings/development.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Production (SMTP)**
```bash
# .env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### SMS/WhatsApp Configuration
```bash
# .env  (get values from https://console.twilio.com/)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+14155551234
TWILIO_WHATSAPP_FROM=+14155238886
# Local: True until credentials work. Production: False
TWILIO_ALLOW_MOCK=False
```

Verify setup:
```bash
python manage.py check_twilio
python manage.py check_twilio --send-sms +9198XXXXXXXX
python manage.py check_twilio --send-whatsapp +9198XXXXXXXX
```

Notes:
- `TWILIO_FROM_NUMBER` must be an SMS-capable Twilio number in E.164 (`+` country code).
- WhatsApp sandbox: join the Twilio sandbox first, then use sandbox sender `+14155238886`.
- Trial accounts can only SMS/WhatsApp verified destination numbers.

## Usage Examples

### Chat Notifications
When a user sends a chat message, the recipient automatically receives:
- In-app notification (instant)
- Email notification (if configured)
- SMS notification (if phone number available)

```python
# apps/core/utils.py
notify_message_recipient(booking, sender, message)
```

### Custom Notifications
Send a notification through a specific channel:

```python
from apps.core.notification_service import create_and_send_notification

create_and_send_notification(
    user=user,
    title="Booking Confirmed",
    message="Your booking for Ganesh Puja is confirmed",
    channel='email',
    link='/booking/123/'
)
```

## Automatic Delivery

Notifications are sent automatically when created via Django signals:

```python
# Automatically triggered on creation
Notification.objects.create(
    user=user,
    title="Title",
    message="Message",
    channel='email'  # Sent immediately
)
```

For async processing in production, integrate with Celery:
```python
from celery import shared_task

@shared_task
def send_notification_task(notification_id):
    notification = Notification.objects.get(id=notification_id)
    delivery_service.send_notification(notification)
```

## Testing

### Test Email Delivery
```bash
# Console output (development)
python manage.py shell
>>> from apps.core.email_service import send_email
>>> from apps.accounts.models import CustomUser
>>> user = CustomUser.objects.first()
>>> send_email(user, "Test Subject", "Test message")
```

### Test SMS Delivery (Mock)
```bash
python manage.py shell
>>> from apps.accounts.utils import sms_service
>>> sms_service.send_otp("+919876543210", "123456", "login")
# Output: 📱 MOCK SMS to +919876543210: Your OTP is 123456
```

### Send Pending Notifications
```bash
python manage.py send_notifications --limit=10
```

## Admin Interface

All notifications are visible in Django admin with:
- Delivery status filtering
- Channel filtering
- Delivery error details
- Read status tracking

Navigate to: `/admin/core/notification/`

## Delivery Status Flow

```
pending → sent → delivered
  ↓
  failed → (retry via management command)
```

## Logging

All notification delivery is logged:
- Location: Django logging system
- Log level: INFO for success, ERROR for failures
- Example:
```
INFO: Email sent successfully to user@email.com: Booking Confirmed
ERROR: Failed to send SMS to +919876543210: Invalid phone format
```

## Future Enhancements

1. **WhatsApp Business API Integration**
   - Send messages directly via WhatsApp
   - Two-way chat integration

2. **Celery Task Queue**
   - Asynchronous notification delivery
   - Scheduled reminders (e.g., 24hrs before booking)

3. **Notification Templates**
   - Customizable templates per channel
   - Multi-language support

4. **Delivery Analytics**
   - Track open rates for emails
   - SMS delivery statistics
   - User preference management

## Troubleshooting

### Email not sending
- Check EMAIL_BACKEND configuration
- Verify SMTP credentials in .env
- Check application logs for errors
- Use console backend in development

### SMS not sending
- Verify Twilio credentials
- Check phone number format (+91 for India)
- Confirm Twilio account has SMS balance
- Check delivery_error field in admin

### Notification not created
- Check user has at least one notification channel configured
- Verify no database errors in logs
- Check notification.delivery_status in admin

## Support

For issues with notification delivery:
1. Check the Notification model in admin
2. Review delivery_status and delivery_error fields
3. Check application logs
4. Run `python manage.py send_notifications --limit=5` to retry
