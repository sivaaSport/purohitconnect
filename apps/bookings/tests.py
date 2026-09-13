from decimal import Decimal
from datetime import timedelta
import hmac
import hashlib
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import CustomUser, PurohitProfile, WalletTransaction
from apps.accounts.utils import wallet_service
from apps.core.models import City, Area
from apps.purohits.models import Purohit, PurohitAvailability
from apps.pujas.models import PujaCategory, Puja, PurohitPujaPackage
from apps.bookings.models import Booking


class BookingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.city = City.objects.create(name='TestCity', state='TS')
        self.area = Area.objects.create(city=self.city, name='TestArea', pincode='500001')
        self.customer = CustomUser.objects.create_user(
            username='customer1',
            phone='+919999999991',
            role='customer',
            password='pass1234'
        )
        self.purohit_user = CustomUser.objects.create_user(
            username='purohit1',
            phone='+919999999992',
            role='purohit',
            password='pass1234'
        )
        self.purohit_profile = PurohitProfile.objects.create(user=self.purohit_user)
        self.purohit = Purohit.objects.create(
            profile=self.purohit_profile,
            name='Acharya',
            city=self.city,
            base_area=self.area,
            base_price=1500.00
        )
        category = PujaCategory.objects.create(name='Test Category')
        self.puja = Puja.objects.create(
            category=category,
            name='Test Puja',
            description='A test ritual',
            base_duration_hours=1.0
        )
        self.package = PurohitPujaPackage.objects.create(
            purohit=self.purohit,
            puja=self.puja,
            price=2500.00,
            includes_samagri=True,
            samagri_price=300.00
        )
        self.client.force_login(self.customer)

    def test_book_page_keeps_date_from_query(self):
        day = timezone.localdate() + timedelta(days=8)
        url = reverse('bookings:book', args=[self.package.id])
        response = self.client.get(url, {'date': day.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['preselected_date'], day)
        self.assertContains(response, f'data-date="{day.isoformat()}"')
        self.assertContains(response, 'is-selected')

    def test_book_package_redirects_to_payment(self):
        url = reverse('bookings:book', args=[self.package.id])
        response = self.client.post(url, {
            'date': '2026-05-10',
            'time': '09:00',
            'address': 'Test address',
            'city': self.city.id,
            'area': self.area.id,
            'needs_samagri': 'on',
            'special_requests': 'Please arrive early',
        })
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.get(customer=self.customer)
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.total_amount, 2800.00)
        self.assertEqual(
            response.url,
            reverse('bookings:booking_payment', args=[booking.booking_id])
        )

    def test_booking_success_redirects_unpaid_to_payment(self):
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            needs_samagri=True,
            special_requests='Test',
            total_amount=2500.00
        )
        url = reverse('bookings:success', args=[booking.booking_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('bookings:booking_payment', args=[booking.booking_id])
        )

    def test_booking_success_shows_confirmation_when_paid(self):
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            needs_samagri=True,
            special_requests='Test',
            total_amount=2500.00,
            payment_status='success',
            status='confirmed'
        )
        url = reverse('bookings:success', args=[booking.booking_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['payment_confirmed'])
        self.assertIn('https://wa.me/', response.context['wa_link'])

    @patch('apps.bookings.views.razorpay.Client')
    def test_verify_payment_updates_booking(self, mock_client):
        mock_client.return_value.utility.verify_payment_signature.return_value = None
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            needs_samagri=True,
            special_requests='Test',
            total_amount=2500.00,
            razorpay_order_id='order_123'
        )
        url = reverse('bookings:verify_payment')
        response = self.client.post(url, {
            'razorpay_order_id': 'order_123',
            'razorpay_payment_id': 'pay_123',
            'razorpay_signature': 'sig_123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success'})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.payment_status, 'success')
        self.assertIsNone(booking.accepted_at)
        self.assertEqual(booking.lifecycle_label, 'PENDING CONFIRMATION')

    @patch('apps.accounts.payment_service.PaymentProcessor.create_order')
    def test_mixed_payment_debits_wallet_and_creates_order(self, mock_create_order):
        mock_create_order.return_value = {'id': 'order_mixed_123'}
        wallet_service.credit_wallet(self.customer, Decimal('1000.00'), 'top_up', 'seed')
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            needs_samagri=True,
            special_requests='Test',
            total_amount=2800.00
        )
        url = reverse('bookings:booking_payment', args=[booking.booking_id])
        response = self.client.post(url, {'payment_method': 'mixed'})
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.customer.refresh_from_db()
        self.assertEqual(booking.advance_paid, Decimal('1000.00'))
        self.assertEqual(booking.razorpay_order_id, 'order_mixed_123')
        self.assertEqual(self.customer.wallet_balance, Decimal('0.00'))
        self.assertEqual(response.context['razorpay_order_id'], 'order_mixed_123')
        self.assertTrue(response.context['is_partial_payment'])

    def test_razorpay_webhook_captures_booking_payment(self):
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            needs_samagri=True,
            special_requests='Test',
            total_amount=2500.00,
            razorpay_order_id='order_123'
        )

        payload = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_123',
                        'order_id': 'order_123',
                        'status': 'captured',
                        'amount': 250000
                    }
                }
            }
        }
        body = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()

        url = reverse('accounts:razorpay_webhook')
        response = self.client.post(
            url,
            body,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'received', 'message': 'Booking payment confirmed'})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.payment_status, 'success')
        self.assertIsNone(booking.accepted_at)
        self.assertEqual(booking.lifecycle_label, 'PENDING CONFIRMATION')
        self.assertEqual(booking.razorpay_payment_id, 'pay_123')

    def test_razorpay_webhook_finalizes_wallet_topup(self):
        order_id = 'order_wallet_123'
        WalletTransaction.objects.create(
            user=self.customer,
            transaction_type='credit',
            reason='top_up',
            amount=Decimal('100.00'),
            status='pending',
            razorpay_order_id=order_id
        )

        payload = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_wallet_123',
                        'order_id': order_id,
                        'status': 'captured',
                        'amount': 10000
                    }
                }
            }
        }
        body = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()

        url = reverse('accounts:razorpay_webhook')
        response = self.client.post(
            url,
            body,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'received', 'message': 'Wallet topped up with ₹100.00'})

        self.customer.refresh_from_db()
        txn = WalletTransaction.objects.get(razorpay_order_id=order_id)
        self.assertEqual(self.customer.wallet_balance, Decimal('100.00'))
        self.assertEqual(txn.status, 'completed')
        self.assertEqual(txn.razorpay_payment_id, 'pay_wallet_123')

    def test_razorpay_webhook_refunds_wallet_topup(self):
        topup = WalletTransaction.objects.create(
            user=self.customer,
            transaction_type='credit',
            reason='top_up',
            amount=Decimal('100.00'),
            status='completed',
            razorpay_order_id='order_wallet_refund_123',
            razorpay_payment_id='pay_wallet_refund_123'
        )
        self.customer.wallet_balance = Decimal('100.00')
        self.customer.save(update_fields=['wallet_balance'])

        payload = {
            'event': 'refund.processed',
            'payload': {
                'refund': {
                    'entity': {
                        'id': 'refund_123',
                        'payment_id': 'pay_wallet_refund_123',
                        'amount': 10000
                    }
                }
            }
        }
        body = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()

        url = reverse('accounts:razorpay_webhook')
        response = self.client.post(
            url,
            body,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'received', 'message': 'Wallet top-up refunded: ₹100'})

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.wallet_balance, Decimal('0.00'))
        refund_txn = WalletTransaction.objects.filter(reason='refund', razorpay_order_id='order_wallet_refund_123').first()
        self.assertIsNotNone(refund_txn)
        self.assertEqual(refund_txn.amount, Decimal('100.00'))

    def test_razorpay_webhook_processes_withdrawal_payout(self):
        withdrawal_txn = WalletTransaction.objects.create(
            user=self.customer,
            transaction_type='debit',
            reason='withdrawal',
            amount=Decimal('200.00'),
            status='pending',
            reference='withdrawal-request-123'
        )
        self.customer.wallet_balance = Decimal('0.00')
        self.customer.save(update_fields=['wallet_balance'])

        payload = {
            'event': 'payout.processed',
            'payload': {
                'payout': {
                    'entity': {
                        'id': 'payout_123',
                        'status': 'processed',
                        'amount': 20000,
                        'notes': {
                            'withdrawal_reference': 'withdrawal-request-123'
                        }
                    }
                }
            }
        }
        body = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()

        url = reverse('accounts:razorpay_webhook')
        response = self.client.post(
            url,
            body,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'received', 'message': 'Payout completed'})

        withdrawal_txn.refresh_from_db()
        self.assertEqual(withdrawal_txn.status, 'completed')
        self.assertEqual(withdrawal_txn.razorpay_payment_id, 'payout_123')

    def test_wallet_payment_confirms_booking(self):
        # Give customer enough wallet balance to pay
        wallet_service.credit_wallet(self.customer, Decimal('2800.00'), 'top_up', 'Booking wallet top-up')
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            needs_samagri=True,
            special_requests='Test',
            total_amount=2800.00
        )
        url = reverse('bookings:booking_payment', args=[booking.booking_id])
        response = self.client.post(url, {'payment_method': 'wallet'})
        self.assertEqual(response.status_code, 302)
        booking.refresh_from_db()
        self.customer.refresh_from_db()
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.payment_status, 'success')
        self.assertIsNone(booking.accepted_at)
        self.assertEqual(booking.lifecycle_label, 'PENDING CONFIRMATION')
        self.assertEqual(self.customer.wallet_balance, Decimal('0.00'))
        if hasattr(booking, 'advance_paid'):
            self.assertEqual(booking.advance_paid, Decimal('2800.00'))
        self.assertTrue(Booking.objects.filter(booking_id=booking.booking_id).exists())

    def test_wallet_payment_insufficient_balance(self):
        wallet_service.credit_wallet(self.customer, Decimal('1000.00'), 'top_up', 'Partial wallet top-up')
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            needs_samagri=True,
            special_requests='Test',
            total_amount=2800.00
        )
        url = reverse('bookings:booking_payment', args=[booking.booking_id])
        response = self.client.post(url, {'payment_method': 'wallet'})
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.payment_status, 'pending')

    def test_payment_options_mixed_when_partial_wallet(self):
        from apps.bookings.payment_utils import get_booking_payment_options

        wallet_service.credit_wallet(self.customer, Decimal('1000.00'), 'top_up', 'seed')
        options = get_booking_payment_options(self.customer, Decimal('2800.00'))
        self.assertFalse(options['wallet']['available'])
        self.assertTrue(options['razorpay']['available'])
        self.assertIn('mixed', options)
        self.assertEqual(options['mixed']['wallet_amount'], Decimal('1000.00'))
        self.assertEqual(options['mixed']['razorpay_amount'], Decimal('1800.00'))

    @patch('apps.accounts.payment_service.PaymentProcessor.create_order')
    def test_mixed_payment_rolls_back_wallet_when_order_fails(self, mock_create_order):
        mock_create_order.return_value = None
        wallet_service.credit_wallet(self.customer, Decimal('1000.00'), 'top_up', 'seed')
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2800.00
        )
        url = reverse('bookings:booking_payment', args=[booking.booking_id])
        response = self.client.post(url, {'payment_method': 'mixed'})
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.wallet_balance, Decimal('1000.00'))
        self.assertFalse(booking.razorpay_order_id)
        self.assertEqual(booking.payment_status, 'pending')
        self.assertTrue(
            WalletTransaction.objects.filter(
                user=self.customer, reason='refund', reference__contains='rollback'
            ).exists()
        )

    @patch('apps.bookings.payment_utils.PaymentProcessor.verify_payment', return_value=True)
    def test_mixed_payment_verify_completes_booking(self, _mock_verify):
        wallet_service.credit_wallet(self.customer, Decimal('1000.00'), 'top_up', 'seed')
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2800.00,
            advance_paid=Decimal('1000.00'),
            razorpay_order_id='order_mixed_complete'
        )
        wallet_service.debit_wallet(
            self.customer, Decimal('1000.00'), 'booking_payment', reference=f'{booking.booking_id} (partial)'
        )
        session = self.client.session
        session['booking_payment_id'] = booking.booking_id
        session.save()

        url = reverse('bookings:verify_booking_payment', args=[booking.booking_id])
        response = self.client.post(url, {
            'razorpay_order_id': 'order_mixed_complete',
            'razorpay_payment_id': 'pay_mixed_complete',
            'razorpay_signature': 'sig_mixed',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.payment_status, 'success')
        self.assertIsNone(booking.accepted_at)
        self.assertEqual(booking.lifecycle_label, 'PENDING CONFIRMATION')
        self.assertEqual(booking.advance_paid, Decimal('2800.00'))
        self.assertEqual(booking.razorpay_payment_id, 'pay_mixed_complete')

    @patch('apps.bookings.payment_utils.PaymentProcessor.verify_payment', return_value=False)
    def test_verify_booking_payment_rejects_invalid_signature(self, _mock_verify):
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2800.00,
            razorpay_order_id='order_bad_sig'
        )
        url = reverse('bookings:verify_booking_payment', args=[booking.booking_id])
        response = self.client.post(url, {
            'razorpay_order_id': 'order_bad_sig',
            'razorpay_payment_id': 'pay_bad',
            'razorpay_signature': 'bad_sig',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'failed')
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.payment_status, 'pending')

    def test_razorpay_webhook_rejects_invalid_signature(self):
        payload = {
            'event': 'payment.captured',
            'payload': {'payment': {'entity': {'id': 'pay_x', 'order_id': 'order_x'}}}
        }
        body = json.dumps(payload).encode('utf-8')
        url = reverse('accounts:razorpay_webhook')
        response = self.client.post(
            url,
            body,
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='not-a-valid-signature'
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': 'invalid_signature'})

    @patch('apps.accounts.payment_service.PaymentProcessor.create_order')
    def test_full_razorpay_payment_creates_order(self, mock_create_order):
        mock_create_order.return_value = {'id': 'order_full_rzp'}

        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2800.00
        )
        url = reverse('bookings:booking_payment', args=[booking.booking_id])
        response = self.client.post(url, {'payment_method': 'razorpay'})
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.razorpay_order_id, 'order_full_rzp')
        self.assertEqual(response.context['razorpay_order_id'], 'order_full_rzp')
        self.assertEqual(response.context['amount'], booking.total_amount)

    def test_razorpay_mock_checkout_when_keys_missing(self):
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-11',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2800.00
        )
        with self.settings(
            RAZORPAY_KEY_ID='rzp_test_YOUR_KEY_HERE',
            RAZORPAY_KEY_SECRET='YOUR_SECRET_HERE',
            RAZORPAY_ALLOW_MOCK=True,
        ):
            url = reverse('bookings:booking_payment', args=[booking.booking_id])
            response = self.client.post(url, {'payment_method': 'razorpay'})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['is_mock_payment'])
            booking.refresh_from_db()
            self.assertTrue(str(booking.razorpay_order_id).startswith('order_mock_'))

            verify_url = reverse('bookings:verify_booking_payment', args=[booking.booking_id])
            verify_response = self.client.post(verify_url, {
                'razorpay_order_id': booking.razorpay_order_id,
                'razorpay_payment_id': f'pay_mock_{booking.booking_id}',
                'razorpay_signature': 'mock_signature',
            })
            self.assertEqual(verify_response.status_code, 302)
            booking.refresh_from_db()
            self.assertEqual(booking.payment_status, 'success')
            self.assertEqual(booking.status, 'pending')
            self.assertIsNone(booking.accepted_at)
            self.assertEqual(booking.lifecycle_label, 'PENDING CONFIRMATION')

    def test_already_paid_booking_redirects_from_payment_page(self):
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date='2026-05-10',
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2800.00,
            status='confirmed',
            payment_status='success'
        )
        url = reverse('bookings:booking_payment', args=[booking.booking_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('bookings:success', args=[booking.booking_id]))

    def test_customer_can_request_reschedule(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.bookings.utils import request_reschedule, accept_reschedule
        from apps.bookings.models import BookingHistory

        event_date = (timezone.localdate() + timedelta(days=5))
        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date=event_date,
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2500.00,
            status='confirmed',
            payment_status='success'
        )
        success, message = request_reschedule(
            booking,
            suggested_date=(event_date + timedelta(days=2)).isoformat(),
            suggested_time='10:30',
            requested_by=self.customer,
            reason='Travel conflict'
        )
        self.assertTrue(success, message)
        booking.refresh_from_db()
        self.assertEqual(booking.reschedule_status, 'pending')
        self.assertEqual(booking.reschedule_reason, 'Travel conflict')
        self.assertEqual(booking.reschedule_requested_by, self.customer)
        self.assertTrue(booking.reschedule_requested_by_customer)
        self.assertFalse(booking.reschedule_requested_by_purohit)
        self.assertTrue(BookingHistory.objects.filter(booking=booking, event='reschedule_requested').exists())

        success, message = accept_reschedule(booking, self.purohit_user)
        self.assertTrue(success, message)
        booking.refresh_from_db()
        self.assertEqual(booking.reschedule_status, 'accepted')
        self.assertEqual(booking.reschedule_count, 1)
        self.assertEqual(booking.event_date, event_date + timedelta(days=2))

    def test_reschedule_blocked_within_notice_window(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.bookings.utils import request_reschedule

        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date=timezone.localdate() + timedelta(hours=10),
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2500.00,
            status='confirmed',
            payment_status='success'
        )
        # Force near-term date that fails 48h rule
        booking.event_date = timezone.localdate() + timedelta(days=1)
        booking.save(update_fields=['event_date'])

        success, message = request_reschedule(
            booking,
            suggested_date=(timezone.localdate() + timedelta(days=3)).isoformat(),
            suggested_time='11:00',
            requested_by=self.purohit_user
        )
        self.assertFalse(success)
        self.assertIn('48 hours', message)

    def test_reschedule_max_count_enforced(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.bookings.utils import request_reschedule

        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date=timezone.localdate() + timedelta(days=7),
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2500.00,
            status='confirmed',
            payment_status='success',
            reschedule_count=2
        )
        success, message = request_reschedule(
            booking,
            suggested_date=(timezone.localdate() + timedelta(days=9)).isoformat(),
            suggested_time='11:00',
            requested_by=self.purohit_user
        )
        self.assertFalse(success)
        self.assertIn('Maximum of 2', message)

    def test_expire_pending_reschedule(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.bookings.utils import expire_pending_reschedule
        from apps.bookings.models import BookingHistory

        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date=timezone.localdate() + timedelta(days=7),
            event_time='09:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2500.00,
            status='confirmed',
            payment_status='success',
            reschedule_status='pending',
            suggested_date=timezone.localdate() + timedelta(days=8),
            reschedule_requested_by=self.purohit_user,
            reschedule_requested_at=timezone.now() - timedelta(hours=25)
        )
        success, message = expire_pending_reschedule(booking)
        self.assertTrue(success, message)
        booking.refresh_from_db()
        self.assertEqual(booking.reschedule_status, 'rejected')
        self.assertIsNone(booking.suggested_date)
        self.assertTrue(BookingHistory.objects.filter(booking=booking, event='reschedule_expired').exists())

    def test_start_ritual_notifies_devotee_and_changes_live_pulse(self):
        from apps.core.models import Notification

        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date=timezone.localdate() + timedelta(days=1),
            event_time='10:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2500.00,
            status='confirmed',
            payment_status='success',
            accepted_at=timezone.now(),
        )
        self.client.force_login(self.customer)
        before = self.client.get(reverse('dashboard:live_pulse'))
        self.assertEqual(before.status_code, 200)
        first = before.json()['fingerprint']
        again = self.client.get(reverse('dashboard:live_pulse'))
        self.assertEqual(again.json()['fingerprint'], first)
        self.assertIn(f'{booking.booking_id}:confirmed:success:none:0:0', first)

        self.client.force_login(self.purohit_user)
        start = self.client.post(reverse('dashboard:update_booking', args=[booking.booking_id]), {
            'status': 'confirmed',
            'verification_code': booking.start_code,
        })
        self.assertEqual(start.status_code, 302)
        booking.refresh_from_db()
        self.assertTrue(booking.started_at)
        self.assertTrue(
            Notification.objects.filter(user=self.customer, title='Ritual started').exists()
        )

        self.client.force_login(self.customer)
        after = self.client.get(reverse('dashboard:live_pulse'))
        self.assertEqual(after.status_code, 200)
        self.assertNotEqual(after.json()['fingerprint'], first)
        self.assertContains(
            self.client.get(reverse('dashboard:customer')),
            'watchDevoteeLive',
        )

    def test_complete_ritual_asks_devotee_for_review(self):
        from apps.core.models import Notification

        booking = Booking.objects.create(
            customer=self.customer,
            purohit=self.purohit,
            puja_package=self.package,
            event_date=timezone.localdate(),
            event_time='10:00',
            address='Test address',
            city=self.city,
            area=self.area,
            total_amount=2500.00,
            status='confirmed',
            payment_status='success',
            accepted_at=timezone.now(),
            started_at=timezone.now(),
        )
        self.client.force_login(self.purohit_user)
        done = self.client.post(reverse('dashboard:update_booking', args=[booking.booking_id]), {
            'status': 'completed',
            'verification_code': booking.complete_code,
        })
        self.assertEqual(done.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'completed')
        note = Notification.objects.filter(user=self.customer, title='Please review your ritual').first()
        self.assertIsNotNone(note)
        self.assertIn('review', note.message.lower())

        self.client.force_login(self.customer)
        page = self.client.get(reverse('dashboard:customer'))
        self.assertContains(page, 'Write a review')
        self.assertContains(page, 'Please share a short review')
        self.assertEqual(page.context['review_prompt']['booking_id'], booking.booking_id)
