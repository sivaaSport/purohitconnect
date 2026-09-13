import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not installed. SMS OTP will use mock delivery.")


class SMSService:
    """SMS / WhatsApp delivery via Twilio (with safe mock fallback for development)."""

    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
        self.whatsapp_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
        self.allow_mock = getattr(settings, 'TWILIO_ALLOW_MOCK', True)
        self.client = None

        if TWILIO_AVAILABLE and self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None

    def is_configured(self):
        """Check if Twilio SMS is properly configured."""
        return bool(TWILIO_AVAILABLE and self.client and self.from_number)

    def is_whatsapp_configured(self):
        """Check if Twilio WhatsApp sender is configured."""
        return bool(TWILIO_AVAILABLE and self.client and self.whatsapp_from)

    def _normalize_phone(self, phone_number):
        if not phone_number:
            return None
        phone_number = str(phone_number).strip()
        if not phone_number.startswith('+'):
            phone_number = f'+{phone_number}'
        return phone_number

    def _whatsapp_address(self, phone_or_sender):
        value = str(phone_or_sender).strip()
        if value.startswith('whatsapp:'):
            return value
        return f"whatsapp:{self._normalize_phone(value)}"

    def _mock_or_fail(self, channel, phone_number, body):
        if self.allow_mock:
            logger.info(f"MOCK {channel.upper()}: Would send to {phone_number}: {body[:120]}")
            try:
                print(f"[MOCK {channel.upper()}] to {phone_number}: {body}")
            except UnicodeEncodeError:
                # Windows consoles may not support all unicode characters
                print(f"[MOCK {channel.upper()}] to {phone_number}: {body.encode('ascii', 'replace').decode('ascii')}")
            return True, f"Mock {channel} sent (check console)", f"mock_{channel}_sid"
        return False, f"{channel.upper()} delivery is not configured", None

    def send_sms(self, phone_number, body):
        """
        Send a general SMS message.

        Returns:
            tuple: (success: bool, message: str, sid: str|None)
        """
        phone_number = self._normalize_phone(phone_number)
        if not phone_number:
            return False, "Phone number is required", None

        body = (body or '').strip()
        if not body:
            return False, "Message body is required", None

        if not self.is_configured():
            return self._mock_or_fail('sms', phone_number, body)

        try:
            message = self.client.messages.create(
                body=body[:1600],
                from_=self.from_number,
                to=phone_number
            )
            logger.info(f"SMS sent to {phone_number}, SID: {message.sid}")
            return True, "SMS sent successfully", message.sid
        except Exception as e:
            logger.error(f"Twilio SMS error to {phone_number}: {str(e)}")
            return False, f"Failed to send SMS: {str(e)}", None

    def send_whatsapp(self, phone_number, body):
        """
        Send a WhatsApp message via Twilio WhatsApp channel.

        Returns:
            tuple: (success: bool, message: str, sid: str|None)
        """
        phone_number = self._normalize_phone(phone_number)
        if not phone_number:
            return False, "Phone number is required", None

        body = (body or '').strip()
        if not body:
            return False, "Message body is required", None

        if not self.is_whatsapp_configured():
            return self._mock_or_fail('whatsapp', phone_number, body)

        try:
            message = self.client.messages.create(
                body=body[:1600],
                from_=self._whatsapp_address(self.whatsapp_from),
                to=self._whatsapp_address(phone_number)
            )
            logger.info(f"WhatsApp sent to {phone_number}, SID: {message.sid}")
            return True, "WhatsApp message sent successfully", message.sid
        except Exception as e:
            logger.error(f"Twilio WhatsApp error to {phone_number}: {str(e)}")
            return False, f"Failed to send WhatsApp message: {str(e)}", None

    def send_otp(self, phone_number, otp_code, otp_type='login'):
        """
        Send OTP via SMS.

        Returns:
            tuple: (success: bool, message: str, sid: str or None)
        """
        messages_map = {
            'login': f'Your PurohitConnect login OTP is: {otp_code}. Valid for 5 minutes.',
            'signup': f'Welcome to PurohitConnect! Your verification OTP is: {otp_code}. Valid for 5 minutes.',
            'verification': f'Your phone verification OTP is: {otp_code}. Valid for 5 minutes.',
        }
        message_body = messages_map.get(otp_type, f'Your OTP is: {otp_code}. Valid for 5 minutes.')
        return self.send_sms(phone_number, message_body)

    def _mock_send_otp(self, phone_number, otp_code, otp_type='login'):
        """Backward-compatible mock OTP helper."""
        return self.send_otp(phone_number, otp_code, otp_type)


# Global SMS service instance
sms_service = SMSService()


def send_otp_sms(phone_number, otp_code, otp_type='login'):
    """
    Convenience function to send OTP SMS

    Args:
        phone_number (str): Phone number
        otp_code (str): OTP code
        otp_type (str): OTP type

    Returns:
        tuple: (success: bool, message: str, sid: str|None)
    """
    return sms_service.send_otp(phone_number, otp_code, otp_type)


def send_sms_message(phone_number, body):
    """Convenience function for general SMS delivery."""
    return sms_service.send_sms(phone_number, body)


def send_whatsapp_message(phone_number, body):
    """Convenience function for WhatsApp delivery."""
    return sms_service.send_whatsapp(phone_number, body)


# Wallet Service Utilities
from decimal import Decimal
from django.db import transaction
from django.db import models
from django.utils import timezone
from .models import CustomUser, WalletTransaction


class WalletService:
    """Service class for managing wallet operations"""
    
    @staticmethod
    def get_balance(user):
        """Get current wallet balance for a user"""
        return Decimal(str(user.wallet_balance or 0))
    
    @staticmethod
    def credit_wallet(user, amount, reason, reference="", razorpay_order_id=None, 
                     razorpay_payment_id=None, razorpay_signature=None):
        """
        Credit amount to user's wallet
        
        Args:
            user: CustomUser instance
            amount: Decimal amount to credit
            reason: Transaction reason (top_up, refund, etc.)
            reference: Optional reference (booking ID, etc.)
            razorpay_order_id: Optional Razorpay order ID
            razorpay_payment_id: Optional Razorpay payment ID
            razorpay_signature: Optional Razorpay signature
        
        Returns:
            tuple: (success: bool, transaction: WalletTransaction or None, message: str)
        """
        if amount <= 0:
            return False, None, "Amount must be positive"
        
        try:
            with transaction.atomic():
                # Create transaction record
                wallet_txn = WalletTransaction.objects.create(
                    user=user,
                    transaction_type='credit',
                    reason=reason,
                    amount=amount,
                    reference=reference,
                    razorpay_order_id=razorpay_order_id,
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_signature=razorpay_signature,
                    status='completed'
                )
                
                # Update user balance
                current_balance = Decimal(str(user.wallet_balance or 0))
                user.wallet_balance = current_balance + amount
                user.save(update_fields=['wallet_balance'])
                
                logger.info(f"Wallet credited: {user.username} +₹{amount} ({reason})")
                return True, wallet_txn, f"Wallet credited with ₹{amount}"
                
        except Exception as e:
            logger.error(f"Wallet credit failed for {user.username}: {str(e)}")
            return False, None, f"Failed to credit wallet: {str(e)}"

    @staticmethod
    def create_pending_credit(user, amount, reason, reference="", razorpay_order_id=None):
        """
        Create a pending wallet top-up transaction without changing balance.
        """
        if amount <= 0:
            return False, None, "Amount must be positive"

        try:
            wallet_txn = WalletTransaction.objects.create(
                user=user,
                transaction_type='credit',
                reason=reason,
                amount=amount,
                reference=reference,
                razorpay_order_id=razorpay_order_id,
                status='pending'
            )
            logger.info(f"Pending wallet top-up created: {user.username} +₹{amount} ({razorpay_order_id})")
            return True, wallet_txn, "Pending wallet top-up created"
        except Exception as e:
            logger.error(f"Failed to create pending wallet credit for {user.username}: {str(e)}")
            return False, None, f"Failed to create pending wallet top-up: {str(e)}"

    @staticmethod
    def finalize_pending_credit(user, amount, razorpay_order_id, razorpay_payment_id=None, razorpay_signature=None):
        """
        Finalize a pending wallet top-up transaction and credit the user's wallet.
        """
        try:
            pending_txn = WalletTransaction.objects.filter(
                user=user,
                razorpay_order_id=razorpay_order_id,
                status='pending'
            ).order_by('-created_at').first()

            if not pending_txn:
                return WalletService.credit_wallet(
                    user,
                    amount,
                    'top_up',
                    reference=f"topup-{razorpay_order_id}",
                    razorpay_order_id=razorpay_order_id,
                    razorpay_payment_id=razorpay_payment_id,
                    razorpay_signature=razorpay_signature
                )

            current_amount = Decimal(str(pending_txn.amount or 0))
            if current_amount != Decimal(str(amount)):
                return False, None, "Payment amount does not match pending top-up"

            with transaction.atomic():
                pending_txn.status = 'completed'
                pending_txn.razorpay_payment_id = razorpay_payment_id
                pending_txn.razorpay_signature = razorpay_signature
                pending_txn.save(update_fields=['status', 'razorpay_payment_id', 'razorpay_signature'])

                current_balance = Decimal(str(user.wallet_balance or 0))
                user.wallet_balance = current_balance + current_amount
                user.save(update_fields=['wallet_balance'])

                logger.info(f"Pending wallet top-up completed: {user.username} +₹{current_amount}")
                return True, pending_txn, f"Wallet topped up with ₹{current_amount}"
        except Exception as e:
            logger.error(f"Failed to finalize pending wallet top-up for {user.username}: {str(e)}")
            return False, None, f"Failed to finalize pending wallet top-up: {str(e)}"

    @staticmethod
    def debit_wallet(user, amount, reason, reference="", razorpay_order_id=None):
        """
        Debit amount from user's wallet
        
        Args:
            user: CustomUser instance
            amount: Decimal amount to debit
            reason: Transaction reason (booking_payment, withdrawal, etc.)
            reference: Optional reference (booking ID, etc.)
            razorpay_order_id: Optional Razorpay order ID
        
        Returns:
            tuple: (success: bool, transaction: WalletTransaction or None, message: str)
        """
        if amount <= 0:
            return False, None, "Amount must be positive"
        
        current_balance = Decimal(str(user.wallet_balance or 0))
        if current_balance < amount:
            return False, None, f"Insufficient balance. Available: ₹{current_balance}"
        
        try:
            with transaction.atomic():
                # Create transaction record
                wallet_txn = WalletTransaction.objects.create(
                    user=user,
                    transaction_type='debit',
                    reason=reason,
                    amount=amount,
                    reference=reference,
                    razorpay_order_id=razorpay_order_id,
                    status='completed'
                )
                
                # Update user balance
                user.wallet_balance = current_balance - amount
                user.save(update_fields=['wallet_balance'])
                
                logger.info(f"Wallet debited: {user.username} -₹{amount} ({reason})")
                return True, wallet_txn, f"Wallet debited by ₹{amount}"
                
        except Exception as e:
            logger.error(f"Wallet debit failed for {user.username}: {str(e)}")
            return False, None, f"Failed to debit wallet: {str(e)}"

    @staticmethod
    def create_pending_debit(user, amount, reason, reference="", razorpay_payment_id=None):
        """
        Reserve funds with a pending debit (used for withdrawals awaiting payout).
        """
        if amount <= 0:
            return False, None, "Amount must be positive"

        current_balance = Decimal(str(user.wallet_balance or 0))
        if current_balance < amount:
            return False, None, f"Insufficient balance. Available: ₹{current_balance}"

        try:
            with transaction.atomic():
                wallet_txn = WalletTransaction.objects.create(
                    user=user,
                    transaction_type='debit',
                    reason=reason,
                    amount=amount,
                    reference=reference,
                    razorpay_payment_id=razorpay_payment_id,
                    status='pending'
                )
                user.wallet_balance = current_balance - amount
                user.save(update_fields=['wallet_balance'])
                logger.info(f"Pending wallet debit created: {user.username} -₹{amount} ({reason})")
                return True, wallet_txn, f"Withdrawal of ₹{amount} reserved"
        except Exception as e:
            logger.error(f"Pending debit failed for {user.username}: {str(e)}")
            return False, None, f"Failed to reserve withdrawal: {str(e)}"
    
    @staticmethod
    def transfer_funds(from_user, to_user, amount, reason, reference=""):
        """
        Transfer funds between two users' wallets
        
        Args:
            from_user: CustomUser instance (sender)
            to_user: CustomUser instance (receiver)
            amount: Decimal amount to transfer
            reason: Transaction reason
            reference: Optional reference
        
        Returns:
            tuple: (success: bool, transactions: tuple or None, message: str)
        """
        if amount <= 0:
            return False, None, "Amount must be positive"
        
        current_balance_from = Decimal(str(from_user.wallet_balance or 0))
        if current_balance_from < amount:
            return False, None, f"Insufficient balance. Available: ₹{current_balance_from}"
        
        try:
            with transaction.atomic():
                # Debit from sender
                debit_txn = WalletTransaction.objects.create(
                    user=from_user,
                    transaction_type='debit',
                    reason=reason,
                    amount=amount,
                    reference=reference,
                    status='completed'
                )
                
                # Credit to receiver
                credit_txn = WalletTransaction.objects.create(
                    user=to_user,
                    transaction_type='credit',
                    reason=reason,
                    amount=amount,
                    reference=reference,
                    status='completed'
                )
                
                # Update balances
                from_user.wallet_balance = current_balance_from - amount
                to_user.wallet_balance = Decimal(str(to_user.wallet_balance or 0)) + amount
                from_user.save(update_fields=['wallet_balance'])
                to_user.save(update_fields=['wallet_balance'])
                
                logger.info(f"Wallet transfer: {from_user.username} -> {to_user.username} ₹{amount} ({reason})")
                return True, (debit_txn, credit_txn), f"₹{amount} transferred successfully"
                
        except Exception as e:
            logger.error(f"Wallet transfer failed: {from_user.username} -> {to_user.username}: {str(e)}")
            return False, None, f"Failed to transfer funds: {str(e)}"
    
    @staticmethod
    def get_transaction_history(user, limit=50):
        """Get user's wallet transaction history"""
        return WalletTransaction.objects.filter(user=user).order_by('-created_at')[:limit]
    
    @staticmethod
    def calculate_wallet_stats(user):
        """Calculate wallet statistics for a user"""
        transactions = WalletTransaction.objects.filter(user=user)
        
        total_credited = transactions.filter(transaction_type='credit').aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        total_debited = transactions.filter(transaction_type='debit').aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        return {
            'current_balance': Decimal(str(user.wallet_balance or 0)),
            'total_credited': total_credited,
            'total_debited': total_debited,
            'transaction_count': transactions.count()
        }


# Global wallet service instance
wallet_service = WalletService()


def credit_wallet(user, amount, reason, reference="", **kwargs):
    """Convenience function to credit wallet"""
    return wallet_service.credit_wallet(user, amount, reason, reference, **kwargs)


def debit_wallet(user, amount, reason, reference="", **kwargs):
    """Convenience function to debit wallet"""
    return wallet_service.debit_wallet(user, amount, reason, reference, **kwargs)


def get_wallet_balance(user):
    """Convenience function to get wallet balance"""
    return wallet_service.get_balance(user)