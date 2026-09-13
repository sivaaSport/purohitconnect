"""
Payment processing utilities for Razorpay integration
Handles wallet top-ups and booking payment processing
"""

import razorpay
import hmac
import hashlib
import json
import logging
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from .utils import wallet_service, credit_wallet, debit_wallet
from apps.accounts.models import CustomUser, WalletTransaction
from apps.bookings.models import Booking
from apps.bookings.utils import record_booking_history
from apps.core.models import Notification

logger = logging.getLogger(__name__)

_PLACEHOLDER_FRAGMENTS = (
    'YOUR_KEY',
    'YOUR_SECRET',
    'your_live',
    'your_secret',
    'CHANGE_ME',
    'changeme',
)


def is_razorpay_configured():
    """True when Razorpay key id/secret look like real credentials."""
    key_id = (getattr(settings, 'RAZORPAY_KEY_ID', None) or '').strip()
    secret = (getattr(settings, 'RAZORPAY_KEY_SECRET', None) or '').strip()
    if not key_id or not secret:
        return False
    combined = f'{key_id} {secret}'.lower()
    if any(fragment.lower() in combined for fragment in _PLACEHOLDER_FRAGMENTS):
        return False
    return key_id.startswith(('rzp_test_', 'rzp_live_'))


def allow_razorpay_mock():
    """Allow local mock checkout when real Razorpay is not configured."""
    return bool(getattr(settings, 'RAZORPAY_ALLOW_MOCK', False)) and not is_razorpay_configured()


# Initialize Razorpay client
try:
    if is_razorpay_configured():
        razorpay_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        RAZORPAY_AVAILABLE = True
    else:
        razorpay_client = None
        RAZORPAY_AVAILABLE = False
        if allow_razorpay_mock():
            logger.warning("Razorpay not configured — mock checkout enabled for local development.")
        else:
            logger.warning("Razorpay not configured and mock checkout is disabled.")
except Exception as e:
    logger.warning(f"Razorpay not configured: {str(e)}")
    RAZORPAY_AVAILABLE = False
    razorpay_client = None


class PaymentProcessor:
    """Handle payment processing through Razorpay"""

    @staticmethod
    def create_mock_order(amount, reference_id):
        """Create a local mock order when Razorpay credentials are unavailable."""
        import time
        amount_paise = int(Decimal(str(amount)) * 100)
        order_id = f"order_mock_{int(time.time())}_{abs(hash(str(reference_id))) % 100000}"
        logger.info(f"MOCK Razorpay order created: {order_id} for {amount} INR")
        return {
            'id': order_id,
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': str(reference_id)[:40],
            'status': 'created',
            'mock': True,
        }
    
    @staticmethod
    def create_order(amount, reference_id, description="", customer_email=None, customer_phone=None):
        """
        Create a Razorpay order for payment
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            reference_id: Unique reference ID (booking ID, user ID, etc.)
            description: Order description
            customer_email: Customer email
            customer_phone: Customer phone
            
        Returns:
            dict: Order details with order_id, or None if failed
        """
        if not RAZORPAY_AVAILABLE or not razorpay_client:
            if allow_razorpay_mock():
                return PaymentProcessor.create_mock_order(amount, reference_id)
            logger.error("Razorpay not available for order creation")
            return None
        
        try:
            amount_paise = int(Decimal(str(amount)) * 100)
            
            order_data = {
                'amount': amount_paise,
                'currency': 'INR',
                'receipt': str(reference_id)[:40],
                'notes': {'description': description or ''},
            }
            
            order = razorpay_client.order.create(data=order_data)
            logger.info(f"Razorpay order created: {order['id']} for {amount} INR")
            return order
            
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            if allow_razorpay_mock():
                logger.warning("Falling back to mock Razorpay order after API failure.")
                return PaymentProcessor.create_mock_order(amount, reference_id)
            return None
    
    @staticmethod
    def verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verify Razorpay payment signature
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Payment signature
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if (
            allow_razorpay_mock()
            and str(razorpay_order_id or '').startswith('order_mock_')
            and str(razorpay_payment_id or '').startswith('pay_mock_')
            and str(razorpay_signature or '') == 'mock_signature'
        ):
            return True

        if not RAZORPAY_AVAILABLE or not razorpay_client:
            return False
        
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            logger.info(f"Payment verified: {razorpay_payment_id}")
            return True
        except Exception as e:
            logger.error(f"Razorpay signature verification failed: {str(e)}")
            return False

    @staticmethod
    def verify_webhook_signature(payload, razorpay_signature):
        """
        Verify Razorpay webhook payload signature.
        Prefer dedicated webhook secret; fall back to key secret.
        """
        if not razorpay_signature:
            return False

        secret_value = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None) or settings.RAZORPAY_KEY_SECRET
        secret = secret_value.encode('utf-8')
        generated_signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(generated_signature, razorpay_signature)

    @staticmethod
    def ensure_razorpay_contact(bank_account):
        """Create or return RazorpayX contact for a bank account holder."""
        if not RAZORPAY_AVAILABLE or not razorpay_client:
            return None, 'Razorpay not configured'

        if bank_account.razorpay_contact_id:
            return bank_account.razorpay_contact_id, 'Contact already exists'

        user = bank_account.user
        try:
            contact = razorpay_client.contact.create({
                'name': bank_account.account_holder_name[:50],
                'email': user.email or None,
                'contact': user.phone or None,
                'type': 'vendor',
                'reference_id': f'user-{user.id}',
                'notes': {
                    'user_id': str(user.id),
                    'username': user.username,
                }
            })
            bank_account.razorpay_contact_id = contact['id']
            bank_account.save(update_fields=['razorpay_contact_id', 'updated_at'])
            return contact['id'], 'Contact created'
        except Exception as e:
            logger.error(f"RazorpayX contact creation failed: {str(e)}")
            return None, str(e)

    @staticmethod
    def ensure_razorpay_fund_account(bank_account):
        """Create or return RazorpayX fund account for bank details."""
        if not RAZORPAY_AVAILABLE or not razorpay_client:
            return None, 'Razorpay not configured'

        if bank_account.razorpay_fund_account_id:
            return bank_account.razorpay_fund_account_id, 'Fund account already exists'

        contact_id, message = PaymentProcessor.ensure_razorpay_contact(bank_account)
        if not contact_id:
            return None, message

        try:
            fund_account = razorpay_client.fund_account.create({
                'contact_id': contact_id,
                'account_type': 'bank_account',
                'bank_account': {
                    'name': bank_account.account_holder_name[:50],
                    'ifsc': bank_account.ifsc_code.upper(),
                    'account_number': bank_account.account_number,
                }
            })
            bank_account.razorpay_fund_account_id = fund_account['id']
            bank_account.save(update_fields=['razorpay_fund_account_id', 'updated_at'])
            return fund_account['id'], 'Fund account created'
        except Exception as e:
            logger.error(f"RazorpayX fund account creation failed: {str(e)}")
            return None, str(e)

    @staticmethod
    def create_payout(bank_account, amount, withdrawal_reference, narration='PurohitConnect withdrawal'):
        """
        Create a RazorpayX payout to the given bank account.

        Returns:
            tuple: (success: bool, payout: dict|None, message: str)
        """
        if not RAZORPAY_AVAILABLE or not razorpay_client:
            return False, None, 'Razorpay not configured'

        account_number = getattr(settings, 'RAZORPAYX_ACCOUNT_NUMBER', None)
        if not account_number:
            return False, None, 'RAZORPAYX_ACCOUNT_NUMBER is not configured'

        fund_account_id, message = PaymentProcessor.ensure_razorpay_fund_account(bank_account)
        if not fund_account_id:
            return False, None, message

        try:
            amount_paise = int(Decimal(str(amount)) * 100)
            payout = razorpay_client.payout.create({
                'account_number': account_number,
                'fund_account_id': fund_account_id,
                'amount': amount_paise,
                'currency': 'INR',
                'mode': getattr(settings, 'RAZORPAYX_PAYOUT_MODE', 'IMPS'),
                'purpose': 'payout',
                'queue_if_low_balance': True,
                'reference_id': withdrawal_reference[:40],
                'narration': narration[:30],
                'notes': {
                    'withdrawal_reference': withdrawal_reference,
                    'user_id': str(bank_account.user_id),
                }
            })
            logger.info(f"RazorpayX payout created: {payout.get('id')} for {amount} INR")
            return True, payout, 'Payout initiated'
        except Exception as e:
            logger.error(f"RazorpayX payout creation failed: {str(e)}")
            return False, None, str(e)

    @staticmethod
    def process_webhook_event(data):
        """
        Process Razorpay webhook event data.
        """
        event = data.get('event')
        payload = data.get('payload', {}) or {}
        payment_entity = payload.get('payment', {}).get('entity')
        order_entity = payload.get('order', {}).get('entity')

        def parse_amount(amount_value):
            try:
                return Decimal(str(amount_value)) / 100 if amount_value is not None else None
            except Exception:
                return None

        def handle_refund_event(refund_entity):
            refund_id = refund_entity.get('id')
            payment_id = refund_entity.get('payment_id')
            amount = parse_amount(refund_entity.get('amount'))

            if not payment_id or amount is None:
                return False, None, 'Refund event missing payment_id or amount'

            # If the refund applies to a wallet top-up, reverse the credited wallet amount.
            topup_txn = WalletTransaction.objects.filter(
                razorpay_payment_id=payment_id,
                reason='top_up',
                status='completed'
            ).order_by('-created_at').first()

            if topup_txn:
                if wallet_service.get_balance(topup_txn.user) >= amount:
                    success, refund_txn, message = wallet_service.debit_wallet(
                        topup_txn.user,
                        amount,
                        'refund',
                        reference=f"refund-{refund_id}",
                        razorpay_order_id=topup_txn.razorpay_order_id
                    )
                    if success:
                        logger.info(f"Wallet top-up refunded for payment {payment_id}")
                        return True, refund_txn, f"Wallet top-up refunded: ₹{amount}"

                logger.warning(f"Insufficient wallet balance to reverse refund for payment {payment_id}")
                return False, None, 'Insufficient wallet balance to reverse refund'

            # If refund is for a booking payment, update booking status and history.
            booking = Booking.objects.filter(razorpay_payment_id=payment_id).first()
            if booking:
                booking.payment_status = 'failed'
                booking.status = 'cancelled'
                booking.save(update_fields=['payment_status', 'status', 'updated_at'])

                record_booking_history(
                    booking=booking,
                    event='payment_failed',
                    user=booking.customer,
                    message=f'Refund processed for booking {booking.booking_id}',
                    old_value='success',
                    new_value='failed'
                )
                Notification.objects.create(
                    user=booking.purohit.profile.user,
                    title='Payment Refunded',
                    message=f'Payment for booking {booking.booking_id} has been refunded.',
                    link=f'/dashboard/purohit/'
                )
                return True, booking, 'Booking payment refunded'

            return False, None, 'Refund event not mapped to any transaction'

        def handle_payout_event(payout_entity):
            payout_id = payout_entity.get('id')
            status = payout_entity.get('status')
            amount = parse_amount(payout_entity.get('amount'))
            notes = payout_entity.get('notes', {}) or {}
            withdrawal_ref = notes.get('withdrawal_reference')

            # Map payout to withdrawal transaction by explicit note or payout id.
            txn = None
            if withdrawal_ref:
                txn = WalletTransaction.objects.filter(
                    reference__startswith=withdrawal_ref,
                    status='pending',
                    reason__in=['withdrawal', 'payout']
                ).first()
                if not txn:
                    txn = WalletTransaction.objects.filter(
                        reference__icontains=withdrawal_ref,
                        status='pending',
                        reason__in=['withdrawal', 'payout']
                    ).first()

            if not txn and payout_id:
                txn = WalletTransaction.objects.filter(
                    razorpay_payment_id=payout_id,
                    status='pending',
                    reason__in=['withdrawal', 'payout']
                ).first()

            if not txn:
                return False, None, 'Payout transaction not found'

            if status in ['processed', 'paid', 'successful', 'completed', 'paid_out']:
                txn.status = 'completed'
                if payout_id:
                    txn.razorpay_payment_id = payout_id
                txn.save(update_fields=['status', 'razorpay_payment_id'])
                from apps.accounts.payout_service import sync_withdrawal_from_payout_event
                sync_withdrawal_from_payout_event(txn, status, payout_id=payout_id)

                Notification.objects.create(
                    user=txn.user,
                    title='Payout Processed',
                    message=f'Your withdrawal of ₹{txn.amount} has been processed successfully.',
                    link='/dashboard/'
                )
                return True, txn, 'Payout completed'

            if status in ['failed', 'reversed', 'rejected']:
                restore_amount = amount if amount is not None else Decimal(str(txn.amount))
                refund_ref = f"payout-failed-{payout_id}" if payout_id else f"payout-failed-{txn.id}"
                already_refunded = WalletTransaction.objects.filter(
                    user=txn.user,
                    reason='refund',
                    reference=refund_ref,
                    status='completed',
                ).exists()

                if txn.status == 'pending' and not already_refunded:
                    wallet_service.credit_wallet(
                        txn.user,
                        restore_amount,
                        'refund',
                        reference=refund_ref,
                    )

                txn.status = 'failed'
                if payout_id:
                    txn.razorpay_payment_id = payout_id
                txn.save(update_fields=['status', 'razorpay_payment_id'])
                from apps.accounts.payout_service import sync_withdrawal_from_payout_event
                sync_withdrawal_from_payout_event(txn, status, payout_id=payout_id)

                Notification.objects.create(
                    user=txn.user,
                    title='Payout Failed',
                    message=f'Your withdrawal of ₹{txn.amount} failed. Funds have been restored to your wallet.',
                    link='/dashboard/'
                )
                return True, txn, 'Payout failed and funds restored'

            return True, txn, 'Payout event received'

        def finalize_wallet_topup(order_id, amount, payment_id=None):
            wallet_txn = WalletTransaction.objects.filter(
                razorpay_order_id=order_id,
                status='pending'
            ).order_by('-created_at').first()

            if wallet_txn:
                return wallet_service.finalize_pending_credit(
                    wallet_txn.user,
                    amount,
                    order_id,
                    razorpay_payment_id=payment_id
                )
            return False, None, 'No pending wallet top-up found'

        def handle_booking_capture(order_id, payment_id, amount):
            booking = Booking.objects.filter(razorpay_order_id=order_id).first()
            if not booking:
                return False, None, 'Booking not found'
            if booking.payment_status == 'success':
                return True, booking, 'Booking already confirmed'

            booking.razorpay_payment_id = payment_id
            booking.payment_status = 'success'
            if booking.status not in ('cancelled', 'completed') and not booking.accepted_at:
                booking.status = 'pending'
            booking.payment_at = timezone.now()
            booking.save(update_fields=['razorpay_payment_id', 'payment_status', 'status', 'payment_at', 'updated_at'])

            record_booking_history(
                booking=booking,
                event='payment_success',
                user=booking.customer,
                message=f"Payment of ₹{amount} received via Razorpay for booking {booking.booking_id}",
                old_value='pending',
                new_value='success'
            )

            Notification.objects.create(
                user=booking.purohit.profile.user,
                title='Payment Received',
                message=f'Payment received for booking {booking.booking_id}.',
                link=f'/dashboard/purohit/'
            )
            return True, booking, 'Booking payment confirmed'

        if event.startswith('refund.'):
            refund_entity = data.get('payload', {}).get('refund', {}).get('entity')
            if refund_entity:
                return handle_refund_event(refund_entity)

        if event.startswith('payout.') and order_entity is None:
            payout_entity = data.get('payload', {}).get('payout', {}).get('entity')
            if payout_entity:
                return handle_payout_event(payout_entity)

        if event in ['payment.captured', 'payment.authorized', 'payment.failed'] and payment_entity:
            order_id = payment_entity.get('order_id')
            payment_id = payment_entity.get('id')
            status = payment_entity.get('status')
            amount = parse_amount(payment_entity.get('amount'))

            if not order_id:
                return False, None, 'Order ID missing from payment entity'

            if status == 'captured':
                success, target, message = handle_booking_capture(order_id, payment_id, amount)
                if success and target:
                    return True, target, message

                success, txn, message = finalize_wallet_topup(order_id, amount, payment_id)
                if success:
                    return True, txn, message

                return False, None, message

            if status == 'authorized':
                logger.info(f"Razorpay payment authorized: {payment_id}")
                return True, None, 'Payment authorized'

            if status == 'failed':
                booking = Booking.objects.filter(razorpay_order_id=order_id).first()
                if booking and booking.payment_status != 'failed':
                    booking.payment_status = 'failed'
                    booking.status = 'pending'
                    booking.save(update_fields=['payment_status', 'status', 'updated_at'])
                    record_booking_history(
                        booking=booking,
                        event='payment_failed',
                        user=booking.customer,
                        message=f'Razorpay payment failed for booking {booking.booking_id}',
                        old_value='pending',
                        new_value='failed'
                    )
                    return True, booking, 'Booking payment failed'

                wallet_txn = WalletTransaction.objects.filter(
                    razorpay_order_id=order_id,
                    status='pending'
                ).order_by('-created_at').first()
                if wallet_txn:
                    wallet_txn.status = 'failed'
                    wallet_txn.save(update_fields=['status'])
                    return True, wallet_txn, 'Wallet top-up failed'

                return False, None, 'No booking or wallet transaction found for failed payment'

        if event == 'order.paid' and order_entity:
            order_id = order_entity.get('id')
            receipt = order_entity.get('receipt', '')
            amount = parse_amount(order_entity.get('amount'))

            if receipt.startswith('wallet-topup-') and order_id and amount is not None:
                success, txn, message = finalize_wallet_topup(order_id, amount)
                if success:
                    return True, txn, message

            booking = Booking.objects.filter(razorpay_order_id=order_id).first()
            if booking and booking.payment_status != 'success':
                booking.payment_status = 'success'
                if booking.status not in ('cancelled', 'completed') and not booking.accepted_at:
                    booking.status = 'pending'
                booking.payment_at = timezone.now()
                booking.save(update_fields=['payment_status', 'status', 'payment_at', 'updated_at'])
                record_booking_history(
                    booking=booking,
                    event='payment_success',
                    user=booking.customer,
                    message=f'Booking payment confirmed via webhook for booking {booking.booking_id}',
                    old_value='pending',
                    new_value='success'
                )
                Notification.objects.create(
                    user=booking.purohit.profile.user,
                    title='Payment Received',
                    message=f'Payment received for booking {booking.booking_id}.',
                    link=f'/dashboard/purohit/'
                )
                return True, booking, 'Booking payment confirmed via order.paid'

        logger.info(f"Unhandled Razorpay webhook event: {event}")
        return True, None, 'Event ignored'

    @staticmethod
    def process_payment(user, amount, payment_type, reference_id=None, 
                       razorpay_order_id=None, razorpay_payment_id=None, 
                       razorpay_signature=None):
        """
        Process a payment and update wallet.

        Args:
            user: CustomUser instance
            amount: Amount to process
            payment_type: 'top_up' or 'booking'
            reference_id: Reference ID (booking ID, etc.)
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Razorpay signature

        Returns:
            tuple: (success: bool, message: str, transaction: WalletTransaction or None)
        """
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return False, "Amount must be positive", None
            
            # Verify signature if Razorpay fields provided
            if razorpay_signature and razorpay_order_id and razorpay_payment_id:
                if not PaymentProcessor.verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
                    return False, "Payment verification failed", None
            
            # Process payment
            if payment_type == 'top_up':
                reason = 'top_up'
                success, transaction, message = wallet_service.finalize_pending_credit(
                    user,
                    amount,
                    razorpay_order_id,
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_signature=razorpay_signature
                )
                if not success and razorpay_order_id and reference_id:
                    # Fallback: create a normal top-up transaction if no pending one exists
                    success, transaction, message = wallet_service.credit_wallet(
                        user,
                        amount,
                        reason,
                        reference=reference_id or f"Payment-{timezone.now().timestamp()}",
                        razorpay_order_id=razorpay_order_id,
                        razorpay_payment_id=razorpay_payment_id,
                        razorpay_signature=razorpay_signature
                    )
            elif payment_type == 'booking':
                reason = 'booking_payment'
                success, transaction, message = wallet_service.debit_wallet(
                    user,
                    amount,
                    reason,
                    reference=reference_id,
                    razorpay_order_id=razorpay_order_id
                )
            else:
                return False, f"Unknown payment type: {payment_type}", None
            
            return success, message, transaction if success else None
            
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            return False, f"Payment processing failed: {str(e)}", None


# Convenience functions
def process_wallet_topup(user, amount, razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """Process wallet top-up payment"""
    return PaymentProcessor.process_payment(
        user, amount, 'top_up',
        reference_id=f"topup-{razorpay_order_id}",
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature
    )


def process_booking_payment(user, amount, booking_id, razorpay_order_id=None, razorpay_payment_id=None):
    """Process booking payment"""
    return PaymentProcessor.process_payment(
        user, amount, 'booking',
        reference_id=booking_id,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id
    )


def create_payment_order(amount, reference_id, description=""):
    """Create Razorpay order"""
    return PaymentProcessor.create_order(amount, reference_id, description)
