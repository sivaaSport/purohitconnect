from unittest.mock import patch
from django.test import TestCase, Client
from django.core.management import call_command
from django.urls import reverse
from apps.accounts.models import CustomUser
from apps.core.models import Notification


class NotificationTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='notify_user',
            email='notify@example.com',
            phone='+919999999993',
            role='customer',
            password='pass1234'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test',
            channel='email',
            delivery_status='pending'
        )

    @patch('apps.core.notification_service.email_service.send_notification_email')
    def test_send_notifications_command(self, mock_send_email):
        mock_send_email.return_value = (True, 'message-id-123', None)
        call_command('send_notifications', limit=5)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.delivery_status, 'sent')
        self.assertEqual(self.notification.delivery_reference, 'message-id-123')

    def test_cleanup_otp_command_deletes_expired(self):
        from apps.accounts.models import OTP
        from django.utils import timezone
        from datetime import timedelta

        OTP.objects.create(
            phone='+919999999994',
            otp_code='123456',
            otp_type='login',
            expires_at=timezone.now() - timedelta(minutes=10),
            is_used=False,
            attempts=0,
            max_attempts=3
        )
        call_command('cleanup_otp')
        self.assertFalse(OTP.objects.filter(phone='+919999999994').exists())


class SupportTicketTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='ticket_user',
            email='ticket@example.com',
            phone='+919999999995',
            role='customer',
            password='pass1234'
        )
        self.staff = CustomUser.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            phone='+919999999996',
            role='customer',
            password='pass1234',
            is_staff=True
        )
        self.client.force_login(self.user)

    def test_create_ticket_creates_service_request(self):
        from apps.core.models import ServiceRequest
        url = reverse('core:create_ticket')
        response = self.client.post(url, {
            'category': 'payment',
            'subject': 'Payment failed',
            'description': 'My booking payment did not confirm.',
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        ticket = ServiceRequest.objects.get(user=self.user)
        self.assertEqual(ticket.subject, 'Payment failed')
        self.assertEqual(ticket.category, 'payment')
        self.assertEqual(ticket.priority, 'high')
        self.assertEqual(ticket.status, 'open')
        self.assertTrue(ticket.ticket_id.startswith('SR-'))
        self.assertIn(ticket.ticket_id, response.content.decode())
        self.assertTrue(
            Notification.objects.filter(user=self.staff, title='New Support Ticket').exists()
        )


class NotificationDeliveryTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='sms_user',
            email='sms@example.com',
            phone='+919999999997',
            role='customer',
            password='pass1234'
        )

    def test_sms_channel_uses_dedicated_sender(self):
        from apps.core.notification_service import delivery_service
        notification = Notification.objects.create(
            user=self.user,
            title='Booking Update',
            message='Your booking is confirmed',
            channel='sms',
            delivery_status='pending'
        )
        success, reference, error = delivery_service.send_notification(notification)
        self.assertTrue(success)
        self.assertTrue(str(reference).startswith('mock_'))
        self.assertIsNone(error)

    def test_whatsapp_channel_delivery(self):
        from apps.core.notification_service import delivery_service
        notification = Notification.objects.create(
            user=self.user,
            title='Ritual Started',
            message='Your purohit has started the ritual',
            channel='whatsapp',
            delivery_status='pending',
            link='/dashboard/customer/'
        )
        success, reference, error = delivery_service.send_notification(notification)
        self.assertTrue(success)
        self.assertTrue(str(reference).startswith('mock_'))
        self.assertIsNone(error)
