from django.core.management.base import BaseCommand
from apps.bookings.utils import expire_pending_reschedules


class Command(BaseCommand):
    help = 'Auto-expire pending reschedule requests older than the configured window'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=200, help='Max bookings to process')

    def handle(self, *args, **options):
        expired = expire_pending_reschedules(limit=options['limit'])
        self.stdout.write(self.style.SUCCESS(f'Expired {expired} pending reschedule request(s).'))
