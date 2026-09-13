"""Management command to send pending notifications."""
from django.core.management.base import BaseCommand
from apps.core.notification_service import delivery_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send all pending notifications via configured channels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of notifications to send',
        )
        parser.add_argument(
            '--channel',
            type=str,
            default=None,
            help='Send only notifications for this channel (email, sms, whatsapp, in_app)',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        channel = options['channel']
        
        self.stdout.write(f"Sending pending notifications (limit: {limit})...")
        
        try:
            results = delivery_service.send_pending_notifications(limit=limit)
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ Sent: {results['sent']} notifications")
            )
            
            if results['failed'] > 0:
                self.stdout.write(
                    self.style.WARNING(f"✗ Failed: {results['failed']} notifications")
                )
                
                if results['errors']:
                    self.stdout.write("\nErrors:")
                    for error in results['errors']:
                        self.stdout.write(
                            f"  - Notification {error['notification_id']}: {error['error']}"
                        )
            
            self.stdout.write(
                self.style.SUCCESS('Notification delivery completed!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending notifications: {str(e)}')
            )
            logger.error(f'Error in send_notifications command: {str(e)}', exc_info=True)
