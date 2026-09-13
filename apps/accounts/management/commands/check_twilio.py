from django.core.management.base import BaseCommand
from django.conf import settings

from apps.accounts.utils import SMSService, TWILIO_AVAILABLE


class Command(BaseCommand):
    help = 'Check Twilio SMS/WhatsApp configuration and optionally send a test message'

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-sms',
            dest='send_sms',
            help='Send a test SMS to this E.164 number (e.g. +9198XXXXXXXX)',
        )
        parser.add_argument(
            '--send-whatsapp',
            dest='send_whatsapp',
            help='Send a test WhatsApp message to this E.164 number',
        )

    def handle(self, *args, **options):
        sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None) or ''
        token = getattr(settings, 'TWILIO_AUTH_TOKEN', None) or ''
        from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None) or ''
        wa_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None) or ''
        allow_mock = getattr(settings, 'TWILIO_ALLOW_MOCK', True)

        self.stdout.write('Twilio package installed: %s' % ('yes' if TWILIO_AVAILABLE else 'no'))
        self.stdout.write('TWILIO_ACCOUNT_SID: %s' % (self._mask(sid) if sid else '(missing)'))
        self.stdout.write('TWILIO_AUTH_TOKEN: %s' % ('set' if token else '(missing)'))
        self.stdout.write('TWILIO_FROM_NUMBER: %s' % (from_number or '(missing)'))
        self.stdout.write('TWILIO_WHATSAPP_FROM: %s' % (wa_from or '(missing)'))
        self.stdout.write('TWILIO_ALLOW_MOCK: %s' % allow_mock)

        sms = SMSService()
        if sms.is_configured():
            self.stdout.write(self.style.SUCCESS('SMS: ready for live delivery'))
        elif allow_mock:
            self.stdout.write(self.style.WARNING('SMS: not fully configured — mock mode active'))
        else:
            self.stdout.write(self.style.ERROR('SMS: not configured and mock disabled (OTP will fail)'))

        if sms.is_whatsapp_configured():
            self.stdout.write(self.style.SUCCESS('WhatsApp: ready for live delivery'))
        elif allow_mock:
            self.stdout.write(self.style.WARNING('WhatsApp: not fully configured — mock mode active'))
        else:
            self.stdout.write(self.style.ERROR('WhatsApp: not configured and mock disabled'))

        if options['send_sms']:
            ok, message, msg_sid = sms.send_sms(
                options['send_sms'],
                'PurohitConnect test SMS — Twilio is working.'
            )
            self._report_send('SMS', ok, message, msg_sid)

        if options['send_whatsapp']:
            ok, message, msg_sid = sms.send_whatsapp(
                options['send_whatsapp'],
                'PurohitConnect test WhatsApp — Twilio is working.'
            )
            self._report_send('WhatsApp', ok, message, msg_sid)

        if not options['send_sms'] and not options['send_whatsapp']:
            self.stdout.write('')
            self.stdout.write('Next: paste credentials into .env, set TWILIO_ALLOW_MOCK=False, then:')
            self.stdout.write('  python manage.py check_twilio --send-sms +91XXXXXXXXXX')

    def _mask(self, value):
        value = str(value)
        if len(value) <= 8:
            return '***'
        return f'{value[:4]}...{value[-4:]}'

    def _report_send(self, channel, ok, message, msg_sid):
        if ok:
            self.stdout.write(self.style.SUCCESS(f'{channel} send OK: {message} (sid={msg_sid})'))
        else:
            self.stdout.write(self.style.ERROR(f'{channel} send FAILED: {message}'))
