from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import OTP
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up expired OTP attempts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find expired OTPs
        expired_otps = OTP.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        count = expired_otps.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would delete {count} expired OTP records')
            )
        else:
            deleted, _ = expired_otps.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted} expired OTP records')
            )
            
            logger.info(f'Cleaned up {deleted} expired OTP records')
        
        # Also clean up OTPs with too many attempts
        failed_otps = OTP.objects.filter(
            attempts__gte=OTP._meta.get_field('max_attempts').default
        )
        
        failed_count = failed_otps.count()
        
        if failed_count > 0:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'DRY RUN: Would delete {failed_count} OTP records with max attempts exceeded')
                )
            else:
                deleted, _ = failed_otps.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {deleted} OTP records with max attempts exceeded')
                )
                logger.info(f'Cleaned up {deleted} OTP records with max attempts exceeded')
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('Dry run completed. Use without --dry-run to actually delete records.')
            )