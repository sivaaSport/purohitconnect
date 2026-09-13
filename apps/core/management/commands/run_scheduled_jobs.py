from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run recurring maintenance jobs (reschedule expiry, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-reschedules',
            action='store_true',
            help='Skip expire_pending_reschedules',
        )

    def handle(self, *args, **options):
        if not options['skip_reschedules']:
            from apps.bookings.utils import expire_pending_reschedules
            expired = expire_pending_reschedules()
            self.stdout.write(self.style.SUCCESS(
                f'Expired {expired} pending reschedule request(s).'
            ))

        self.stdout.write(self.style.SUCCESS('Scheduled jobs finished.'))
