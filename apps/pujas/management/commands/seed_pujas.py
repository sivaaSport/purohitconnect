from django.core.management.base import BaseCommand

from apps.pujas.catalog import seed_hindu_pujas


class Command(BaseCommand):
    help = 'Seed the full Hindu puja catalog (idempotent).'

    def handle(self, *args, **options):
        stats = seed_hindu_pujas()
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded Hindu pujas: +{stats["categories_created"]} categories, '
                f'+{stats["pujas_created"]} pujas '
                f'(totals: {stats["category_total"]} categories, {stats["puja_total"]} pujas)'
            )
        )
