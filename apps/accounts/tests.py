from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import CustomUser, OTP, WalletTransaction
from apps.accounts.utils import send_otp_sms, wallet_service


class AccountTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.phone = "+919999999990"
        self.user = CustomUser.objects.create_user(
            username='customer_test',
            phone=self.phone,
            role='customer',
            password='testpass123'
        )

    def test_generate_and_verify_otp(self):
        otp = OTP.generate_otp(self.phone, 'login')
        self.assertFalse(otp.is_used)
        self.assertTrue(otp.is_valid())

        success, message = OTP.verify_otp(self.phone, otp.otp_code, 'login')
        self.assertTrue(success)
        self.assertEqual(message, 'OTP verified successfully')

        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_invalid_otp_attempt(self):
        otp = OTP.generate_otp(self.phone, 'login')
        success, message = OTP.verify_otp(self.phone, '000000', 'login')
        self.assertFalse(success)
        self.assertIn('Invalid OTP', message)
        otp.refresh_from_db()
        self.assertEqual(otp.attempts, 1)
        self.assertEqual(OTP.objects.filter(phone=self.phone, is_used=False).count(), 1)

    def test_otp_lockout_after_max_attempts(self):
        otp = OTP.generate_otp(self.phone, 'login')
        for _ in range(otp.max_attempts):
            success, _message = OTP.verify_otp(self.phone, '000000', 'login')
            self.assertFalse(success)
        success, message = OTP.verify_otp(self.phone, otp.otp_code, 'login')
        self.assertFalse(success)
        self.assertIn('Maximum attempts', message)

    def test_new_otp_invalidates_previous(self):
        first = OTP.generate_otp(self.phone, 'login')
        second = OTP.generate_otp(self.phone, 'login')
        success, _message = OTP.verify_otp(self.phone, first.otp_code, 'login')
        self.assertFalse(success)
        success, _message = OTP.verify_otp(self.phone, second.otp_code, 'login')
        self.assertTrue(success)

    def test_send_otp_sms_mock(self):
        success, message, sid = send_otp_sms(self.phone, '123456', 'login')
        self.assertTrue(success)
        self.assertTrue(str(sid).startswith('mock_'))
        self.assertIn('Mock', message)

    def test_sms_fails_closed_when_mock_disabled(self):
        from apps.accounts.utils import SMSService
        with self.settings(TWILIO_ALLOW_MOCK=False, TWILIO_ACCOUNT_SID=None, TWILIO_AUTH_TOKEN=None, TWILIO_FROM_NUMBER=None):
            service = SMSService()
            success, message, sid = service.send_otp(self.phone, '123456', 'login')
            self.assertFalse(success)
            self.assertIsNone(sid)
            self.assertIn('not configured', message.lower())

    def test_whatsapp_mock_delivery(self):
        from apps.accounts.utils import send_whatsapp_message
        success, message, sid = send_whatsapp_message(self.phone, 'Hello from PurohitConnect')
        self.assertTrue(success)
        self.assertTrue(str(sid).startswith('mock_'))
        self.assertIn('Mock', message)

    def test_send_otp_view_signup(self):
        url = reverse('accounts:send_otp')
        response = self.client.post(url, {
            'phone': '9999999991',
            'action': 'signup',
            'role': 'customer',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:otp_verification'))
        self.assertTrue(OTP.objects.filter(phone='+919999999991').exists())

        verify_page = self.client.get(reverse('accounts:otp_verification'))
        self.assertEqual(verify_page.status_code, 200)
        self.assertContains(verify_page, 'Verify Your Phone')
        from apps.accounts.utils import sms_service
        with self.settings(DEBUG=True):
            debug_page = self.client.get(reverse('accounts:otp_verification'))
        if not sms_service.is_configured():
            self.assertContains(debug_page, 'Development mode')

    def test_wallet_credit_debit_transfer(self):
        success, transaction, message = wallet_service.credit_wallet(
            self.user, Decimal('300.00'), 'top_up', 'Unit test top-up'
        )
        self.assertTrue(success)
        self.assertIsNotNone(transaction)
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, Decimal('300.00'))

        success, transaction, message = wallet_service.debit_wallet(
            self.user, Decimal('100.00'), 'booking_payment', 'Unit test booking payment'
        )
        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, Decimal('200.00'))

        recipient = CustomUser.objects.create_user(
            username='customer_test2',
            phone='+919999999992',
            role='customer',
            password='testpass123'
        )

        success, transactions, message = wallet_service.transfer_funds(
            self.user, recipient, Decimal('50.00'), 'transfer', 'Unit test transfer'
        )
        self.assertTrue(success)
        self.user.refresh_from_db()
        recipient.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, Decimal('150.00'))
        self.assertEqual(recipient.wallet_balance, Decimal('50.00'))
        self.assertEqual(len(transactions), 2)

    def test_wallet_debit_insufficient_balance(self):
        success, transaction, message = wallet_service.debit_wallet(
            self.user, Decimal('10.00'), 'booking_payment', 'Unit test insufficient'
        )
        self.assertFalse(success)
        self.assertIn('Insufficient balance', message)
        self.assertIsNone(transaction)

    def test_wallet_transaction_history(self):
        wallet_service.credit_wallet(self.user, Decimal('150.00'), 'top_up', 'Unit test history')
        transactions = wallet_service.get_transaction_history(self.user, limit=5)
        self.assertEqual(transactions.count(), 1)
        txn = transactions[0]
        self.assertEqual(txn.transaction_type, 'credit')
        self.assertEqual(txn.amount, Decimal('150.00'))

    def test_create_pending_debit_for_withdrawal(self):
        wallet_service.credit_wallet(self.user, Decimal('500.00'), 'top_up', 'seed')
        success, txn, message = wallet_service.create_pending_debit(
            self.user, Decimal('200.00'), 'withdrawal', reference='wd-test-1'
        )
        self.assertTrue(success)
        self.assertEqual(txn.status, 'pending')
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, Decimal('300.00'))

    def test_wallet_withdrawal_creates_bank_account(self):
        from apps.accounts.models import PurohitBankAccount, WithdrawalRequest

        self.user.role = 'purohit'
        self.user.save(update_fields=['role'])
        wallet_service.credit_wallet(self.user, Decimal('1000.00'), 'top_up', 'seed')
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:wallet_withdrawal'), {
            'amount': '250.00',
            'account_holder_name': 'Test User',
            'account_number': '1234567890',
            'ifsc_code': 'HDFC0001234',
            'bank_name': 'HDFC Bank',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PurohitBankAccount.objects.filter(user=self.user).exists())
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, Decimal('750.00'))
        txn = WalletTransaction.objects.filter(user=self.user, reason='withdrawal').latest('created_at')
        self.assertEqual(txn.status, 'pending')
        self.assertTrue(txn.reference.startswith('wd-'))
        withdrawal = WithdrawalRequest.objects.get(wallet_transaction=txn)
        self.assertEqual(withdrawal.status, 'pending_review')
        self.assertEqual(withdrawal.amount, Decimal('250.00'))

    def test_admin_can_reject_withdrawal_and_restore_funds(self):
        from apps.accounts.models import PurohitBankAccount, WithdrawalRequest
        from apps.accounts.payout_service import create_withdrawal_request, reject_withdrawal

        self.user.role = 'purohit'
        self.user.save(update_fields=['role'])
        wallet_service.credit_wallet(self.user, Decimal('500.00'), 'top_up', 'seed')
        bank = PurohitBankAccount.objects.create(
            user=self.user,
            account_holder_name='Test User',
            account_number='1234567890',
            ifsc_code='HDFC0001234',
            bank_name='HDFC'
        )
        ok, withdrawal, _ = create_withdrawal_request(self.user, bank, Decimal('200.00'), 'wd-reject-1')
        self.assertTrue(ok)
        admin = CustomUser.objects.create_superuser(
            username='admin_wd', email='a@test.com', password='pass1234', phone='+919900000099'
        )
        success, message = reject_withdrawal(withdrawal, admin, note='Bad KYC')
        self.assertTrue(success, message)
        withdrawal.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(withdrawal.status, 'rejected')
        self.assertEqual(self.user.wallet_balance, Decimal('500.00'))

    def test_admin_approve_requires_verified_bank(self):
        from apps.accounts.models import PurohitBankAccount
        from apps.accounts.payout_service import create_withdrawal_request, approve_withdrawal

        self.user.role = 'purohit'
        self.user.save(update_fields=['role'])
        wallet_service.credit_wallet(self.user, Decimal('500.00'), 'top_up', 'seed')
        bank = PurohitBankAccount.objects.create(
            user=self.user,
            account_holder_name='Test User',
            account_number='1234567890',
            ifsc_code='HDFC0001234',
            is_verified=False
        )
        ok, withdrawal, _ = create_withdrawal_request(self.user, bank, Decimal('150.00'), 'wd-approve-1')
        self.assertTrue(ok)
        admin = CustomUser.objects.create_superuser(
            username='admin_wd2', email='a2@test.com', password='pass1234', phone='+919900000098'
        )
        success, message = approve_withdrawal(withdrawal, admin, initiate=True)
        self.assertTrue(success)
        self.assertIn('verified', message.lower())
        withdrawal.refresh_from_db()
        self.assertEqual(withdrawal.status, 'approved')
        # Funds remain reserved for retry/reject
        self.user.refresh_from_db()
        self.assertEqual(self.user.wallet_balance, Decimal('350.00'))

    def test_payout_helpers_require_config(self):
        from apps.accounts.models import PurohitBankAccount
        from apps.accounts.payment_service import PaymentProcessor

        bank = PurohitBankAccount.objects.create(
            user=self.user,
            account_holder_name='Test User',
            account_number='1234567890',
            ifsc_code='HDFC0001234',
            bank_name='HDFC'
        )
        success, payout, message = PaymentProcessor.create_payout(
            bank, Decimal('100.00'), 'wd-unit-test'
        )
        self.assertFalse(success)
        self.assertIsNone(payout)
        self.assertTrue(
            'not configured' in message.lower()
            or 'razorpay' in message.lower()
            or 'account_number' in message.lower()
        )

    def test_wallet_topup_mock_checkout(self):
        self.client.force_login(self.user)
        with self.settings(
            RAZORPAY_KEY_ID='rzp_test_YOUR_KEY_HERE',
            RAZORPAY_KEY_SECRET='YOUR_SECRET_HERE',
            RAZORPAY_ALLOW_MOCK=True,
        ):
            response = self.client.post(reverse('accounts:wallet_topup'), {'amount': '4000'})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['is_mock_payment'])
            order_id = response.context['order']['id']
            self.assertTrue(str(order_id).startswith('order_mock_'))

            verify = self.client.post(reverse('accounts:verify_wallet_payment'), {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': f'pay_mock_{order_id}',
                'razorpay_signature': 'mock_signature',
            })
            self.assertEqual(verify.status_code, 302)
            self.user.refresh_from_db()
            self.assertEqual(self.user.wallet_balance, Decimal('4000.00'))

    def test_devotee_dashboard_uses_work_first_layout(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:customer'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Today's work")
        self.assertContains(response, 'Your bookings')
        self.assertContains(response, 'Travel requests')
        self.assertContains(response, 'id="sacred-calendar"')
        self.assertContains(response, 'href="#my-bookings"')
        self.assertNotContains(response, 'ONGOING RITUAL HERO PANEL')
        self.assertIn('bookings_need_you', response.context)
        self.assertIn('bookings_upcoming', response.context)
        self.assertIn('travel_requests', response.context)

    def test_purohit_can_open_devotee_workspace(self):
        from apps.accounts.models import PurohitProfile
        self.user.role = 'purohit'
        self.user.save(update_fields=['role'])
        PurohitProfile.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:customer'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get('active_workspace'), 'devotee')

    def test_switch_workspace_to_devotee(self):
        from apps.accounts.models import PurohitProfile
        self.user.role = 'purohit'
        self.user.save(update_fields=['role'])
        PurohitProfile.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('accounts:switch_workspace'),
            {'workspace': 'devotee', 'next': '/dashboard/purohit/'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:customer'))
        self.assertEqual(self.client.session.get('active_workspace'), 'devotee')

    def test_switch_workspace_to_purohit_via_get(self):
        from apps.accounts.models import PurohitProfile
        self.user.role = 'purohit'
        self.user.save(update_fields=['role'])
        PurohitProfile.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('accounts:switch_workspace'),
            {'workspace': 'purohit'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:purohit'))
        self.assertEqual(self.client.session.get('active_workspace'), 'purohit')
