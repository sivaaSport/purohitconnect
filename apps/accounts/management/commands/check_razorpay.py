from django.core.management.base import BaseCommand
from django.conf import settings

from apps.accounts.payment_service import is_razorpay_configured


class Command(BaseCommand):
    help = 'Check Razorpay checkout and webhook configuration'

    def handle(self, *args, **options):
        key_id = (getattr(settings, 'RAZORPAY_KEY_ID', None) or '').strip()
        secret = (getattr(settings, 'RAZORPAY_KEY_SECRET', None) or '').strip()
        webhook = (getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None) or '').strip()
        allow_mock = bool(getattr(settings, 'RAZORPAY_ALLOW_MOCK', False))
        debug = bool(getattr(settings, 'DEBUG', False))

        self.stdout.write('DEBUG: %s' % debug)
        self.stdout.write('RAZORPAY_KEY_ID: %s' % (self._mask(key_id) if key_id else '(missing)'))
        self.stdout.write('RAZORPAY_KEY_SECRET: %s' % ('set' if secret else '(missing)'))
        self.stdout.write('RAZORPAY_WEBHOOK_SECRET: %s' % ('set' if webhook else '(missing)'))
        self.stdout.write('RAZORPAY_ALLOW_MOCK: %s' % allow_mock)

        if is_razorpay_configured():
            live = key_id.startswith('rzp_live_')
            self.stdout.write(self.style.SUCCESS(
                'Checkout: ready (%s keys)' % ('live' if live else 'test')
            ))
            if live and debug:
                self.stdout.write(self.style.WARNING('Live keys with DEBUG=True — do not use this on a public host.'))
        elif allow_mock:
            self.stdout.write(self.style.WARNING('Checkout: mock mode (local only). Real cards will not be charged.'))
        else:
            self.stdout.write(self.style.ERROR('Checkout: not configured and mock disabled. Pay will fail.'))

        if webhook:
            self.stdout.write(self.style.SUCCESS('Webhook: secret is set'))
        elif allow_mock:
            self.stdout.write(self.style.WARNING(
                'Webhook: no RAZORPAY_WEBHOOK_SECRET — local tests fall back to the API key secret.'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                'Webhook: RAZORPAY_WEBHOOK_SECRET is required when mock is off. '
                'Dashboard → Settings → Webhooks, URL .../accounts/webhook/razorpay/'
            ))

        self.stdout.write('')
        self.stdout.write('Human glance before production:')
        self.stdout.write('  1. Test-mode key, pay INR 1 on Flutter web, confirm booking is paid.')
        self.stdout.write('  2. Paste webhook secret; capture a payment.captured event.')
        self.stdout.write('  3. Switch to rzp_live_ only after that test payment.')
        self.stdout.write('  4. python manage.py check_twilio  (OTP SMS must not be mock).')

    def _mask(self, value):
        value = str(value)
        if len(value) <= 10:
            return '***'
        return f'{value[:8]}...{value[-4:]}'
