"""
Booking payment utilities and handlers
"""

import logging
from django.utils import timezone
from decimal import Decimal
from apps.accounts.utils import wallet_service, debit_wallet
from apps.accounts.payment_service import PaymentProcessor
from apps.core.models import Notification

logger = logging.getLogger(__name__)


def process_booking_payment_wallet(booking, user):
    """
    Process booking payment using wallet balance
    
    Args:
        booking: Booking instance
        user: User instance (should be booking.customer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        amount = Decimal(str(booking.total_amount))
        
        # Check wallet balance
        balance = wallet_service.get_balance(user)
        if balance < amount:
            shortfall = amount - balance
            return False, f"Insufficient wallet balance. Need ₹{shortfall} more"
        
        # Debit wallet
        success, transaction, message = wallet_service.debit_wallet(
            user,
            amount,
            'booking_payment',
            reference=booking.booking_id
        )
        
        if success:
            # Paid, but still awaiting purohit acceptance
            booking.payment_status = 'success'
            booking.payment_at = timezone.now()
            if booking.status not in ('cancelled', 'completed') and not booking.accepted_at:
                booking.status = 'pending'
            booking.advance_paid = amount
            booking.save(update_fields=[
                'payment_status', 'payment_at', 'status',
                'advance_paid', 'updated_at'
            ])
            
            # Record payment in wallet transaction
            transaction.reference = f"{booking.booking_id}"
            transaction.save(update_fields=['reference'])
            
            # Notify purohit
            Notification.objects.create(
                user=booking.purohit.profile.user,
                title="Payment Received!",
                message=f"Payment of ₹{amount} received for booking {booking.booking_id}. Please confirm the booking.",
                link=f"/dashboard/purohit/"
            )
            
            logger.info(f"Booking {booking.booking_id} paid via wallet")
            return True, "Payment successful! Waiting for purohit confirmation."
        else:
            return False, message
            
    except Exception as e:
        logger.error(f"Booking wallet payment error: {str(e)}")
        return False, f"Payment processing failed: {str(e)}"


def process_booking_payment_razorpay(booking, razorpay_order_id, 
                                     razorpay_payment_id, razorpay_signature):
    """
    Process booking payment using Razorpay
    
    Args:
        booking: Booking instance
        razorpay_order_id: Razorpay order ID
        razorpay_payment_id: Razorpay payment ID
        razorpay_signature: Payment signature
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Verify payment signature
        if not PaymentProcessor.verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            return False, "Payment verification failed"
        
        amount = Decimal(str(booking.total_amount))
        
        # For partial payments, calculate the Razorpay amount paid
        razorpay_amount = amount - Decimal(str(booking.advance_paid or 0))
        
        # Update booking — paid, awaiting purohit confirmation
        booking.payment_status = 'success'
        booking.payment_at = timezone.now()
        if booking.status not in ('cancelled', 'completed') and not booking.accepted_at:
            booking.status = 'pending'
        booking.advance_paid = amount  # Now fully paid
        booking.razorpay_payment_id = razorpay_payment_id
        booking.razorpay_signature = razorpay_signature
        booking.save(update_fields=[
            'payment_status', 'payment_at', 'status', 'advance_paid',
            'razorpay_payment_id', 'razorpay_signature', 'updated_at'
        ])
        
        # Create wallet transaction record for audit
        from apps.accounts.models import WalletTransaction
        WalletTransaction.objects.create(
            user=booking.customer,
            transaction_type='debit',
            reason='booking_payment',
            amount=razorpay_amount,  # Only the Razorpay portion
            reference=booking.booking_id,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            status='completed'
        )
        
        # Notify purohit
        Notification.objects.create(
            user=booking.purohit.profile.user,
            title="Payment Received!",
            message=f"Payment of ₹{amount} received for booking {booking.booking_id}." + 
                   (f" (₹{booking.advance_paid - razorpay_amount} from wallet + ₹{razorpay_amount} via Razorpay)" if booking.advance_paid > razorpay_amount else ""),
            link=f"/dashboard/purohit/"
        )
        
        logger.info(f"Booking {booking.booking_id} paid via Razorpay")
        return True, "Payment successful! Waiting for purohit confirmation."
        
    except Exception as e:
        logger.error(f"Booking Razorpay payment error: {str(e)}")
        return False, f"Payment processing failed: {str(e)}"


def get_booking_payment_options(user, booking_amount):
    """
    Get available payment options for a booking
    
    Args:
        user: Customer user instance
        booking_amount: Booking total amount
        
    Returns:
        dict: Available payment options with details
    """
    wallet_balance = wallet_service.get_balance(user)
    amount = Decimal(str(booking_amount))
    
    options = {
        'wallet': {
            'available': wallet_balance >= amount,
            'balance': wallet_balance,
            'shortfall': max(0, amount - wallet_balance),
            'description': 'Pay using your PurohitConnect wallet'
        },
        'razorpay': {
            'available': True,
            'description': 'Pay securely using Razorpay'
        }
    }
    
    # Add mixed payment option if wallet has some balance but not enough for full payment
    if wallet_balance > 0 and wallet_balance < amount:
        options['mixed'] = {
            'available': True,
            'wallet_amount': wallet_balance,
            'razorpay_amount': amount - wallet_balance,
            'description': f'Pay ₹{wallet_balance} from wallet + ₹{amount - wallet_balance} via Razorpay'
        }
    
    return options


def process_booking_payment_mixed(booking, user):
    """
    Process booking payment using mixed wallet + Razorpay
    
    Args:
        booking: Booking instance
        user: User instance (should be booking.customer)
        
    Returns:
        tuple: (success: bool, message: str, razorpay_order: dict or None)
    """
    try:
        amount = Decimal(str(booking.total_amount))
        wallet_balance = wallet_service.get_balance(user)
        
        if wallet_balance <= 0:
            return False, "No wallet balance available for mixed payment", None
            
        if wallet_balance >= amount:
            return False, "Use full wallet payment instead", None
        
        wallet_amount = wallet_balance
        razorpay_amount = amount - wallet_amount
        
        # Debit wallet for the partial amount
        success, transaction, message = wallet_service.debit_wallet(
            user,
            wallet_amount,
            'booking_payment',
            reference=f"{booking.booking_id} (partial)"
        )
        
        if not success:
            return False, f"Failed to debit wallet: {message}", None
        
        # Create Razorpay order for the remaining amount
        try:
            order = PaymentProcessor.create_order(
                razorpay_amount,
                f"booking-{booking.booking_id}-partial-{user.id}-{timezone.now().timestamp()}",
                description=f"Partial payment for booking {booking.booking_id} (₹{razorpay_amount} of ₹{amount})"
            )
            
            if order:
                # Update booking with partial payment info
                booking.advance_paid = wallet_amount
                booking.razorpay_order_id = order['id']
                booking.save(update_fields=['advance_paid', 'razorpay_order_id'])
                
                return True, f"Wallet debited ₹{wallet_amount}. Pay remaining ₹{razorpay_amount} via Razorpay.", order
            else:
                # Rollback wallet debit if Razorpay order creation fails
                wallet_service.credit_wallet(
                    user,
                    wallet_amount,
                    'refund',
                    reference=f"{booking.booking_id} (rollback)"
                )
                return False, "Failed to create Razorpay order", None
                
        except Exception as e:
            # Rollback wallet debit
            wallet_service.credit_wallet(
                user,
                wallet_amount,
                'refund',
                reference=f"{booking.booking_id} (rollback)"
            )
            logger.error(f"Mixed payment Razorpay order creation failed: {str(e)}")
            return False, f"Failed to create payment order: {str(e)}", None
            
    except Exception as e:
        logger.error(f"Mixed payment processing failed: {str(e)}")
        return False, f"Payment processing failed: {str(e)}", None
