"""Withdrawal / payout orchestration helpers."""
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import WithdrawalRequest, WalletTransaction
from apps.accounts.payment_service import PaymentProcessor, RAZORPAY_AVAILABLE
from apps.accounts.utils import wallet_service
from apps.core.models import Notification


def _auto_payout_enabled():
    return bool(getattr(settings, 'WITHDRAWAL_AUTO_PAYOUT', False))


def _require_verified_bank():
    return bool(getattr(settings, 'WITHDRAWAL_REQUIRE_VERIFIED_BANK', True))


def create_withdrawal_request(user, bank_account, amount, withdrawal_ref):
    """
    Reserve wallet funds and create a reviewable withdrawal request.
    Optionally auto-initiates RazorpayX payout when policy allows.
    """
    amount = Decimal(str(amount))
    success, txn, message = wallet_service.create_pending_debit(
        user, amount, 'withdrawal', reference=withdrawal_ref
    )
    if not success:
        return False, None, message

    request_obj = WithdrawalRequest.objects.create(
        user=user,
        bank_account=bank_account,
        wallet_transaction=txn,
        amount=amount,
        status='pending_review',
        withdrawal_reference=withdrawal_ref,
    )

    Notification.objects.create(
        user=user,
        title='Withdrawal Requested',
        message=f'Withdrawal of ₹{amount} is pending review.',
        link='/accounts/wallet/'
    )

    can_auto = (
        _auto_payout_enabled()
        and RAZORPAY_AVAILABLE
        and getattr(settings, 'RAZORPAYX_ACCOUNT_NUMBER', None)
        and (bank_account.is_verified or not _require_verified_bank())
    )
    if can_auto:
        ok, msg = initiate_payout(request_obj)
        if ok:
            return True, request_obj, msg
        return True, request_obj, (
            f"Withdrawal reserved and queued for admin review. Auto-payout failed: {msg}"
        )

    return True, request_obj, (
        f"Withdrawal of ₹{amount} reserved and queued for admin approval."
    )


def initiate_payout(withdrawal: WithdrawalRequest):
    """Send RazorpayX payout for an approved/pending withdrawal."""
    if withdrawal.status in ('completed', 'rejected'):
        return False, f"Cannot payout a {withdrawal.status} withdrawal."

    if _require_verified_bank() and not withdrawal.bank_account.is_verified:
        return False, 'Bank account must be verified before payout.'

    if not RAZORPAY_AVAILABLE or not getattr(settings, 'RAZORPAYX_ACCOUNT_NUMBER', None):
        return False, 'RazorpayX is not configured.'

    txn = withdrawal.wallet_transaction
    if txn.status == 'completed':
        withdrawal.status = 'completed'
        withdrawal.save(update_fields=['status', 'updated_at'])
        return True, 'Withdrawal already completed.'

    success, payout, message = PaymentProcessor.create_payout(
        withdrawal.bank_account,
        withdrawal.amount,
        withdrawal_reference=withdrawal.withdrawal_reference,
        narration='PC Withdrawal'
    )
    withdrawal.payout_attempts += 1
    if success and payout:
        payout_id = payout.get('id')
        withdrawal.status = 'payout_pending'
        withdrawal.razorpay_payout_id = payout_id
        withdrawal.last_error = ''
        withdrawal.save(update_fields=[
            'status', 'razorpay_payout_id', 'payout_attempts', 'last_error', 'updated_at'
        ])
        txn.razorpay_payment_id = payout_id
        txn.status = 'pending'
        txn.reference = f"{withdrawal.withdrawal_reference}|payout:{payout_id}"
        txn.save(update_fields=['razorpay_payment_id', 'reference', 'status'])
        return True, 'Payout initiated with RazorpayX.'

    # Keep funds reserved (txn stays pending) so admin can retry or reject.
    withdrawal.status = 'failed'
    withdrawal.last_error = message or 'Payout creation failed'
    withdrawal.save(update_fields=['status', 'last_error', 'payout_attempts', 'updated_at'])
    return False, withdrawal.last_error


@transaction.atomic
def approve_withdrawal(withdrawal: WithdrawalRequest, admin_user, note: str = '', initiate: bool = True):
    """Admin approves a withdrawal and optionally starts payout."""
    if withdrawal.status not in ('pending_review', 'failed', 'approved'):
        return False, f"Cannot approve withdrawal in status {withdrawal.status}."

    withdrawal.status = 'approved'
    withdrawal.reviewed_by = admin_user
    withdrawal.reviewed_at = timezone.now()
    withdrawal.review_note = (note or '')[:2000]
    withdrawal.save(update_fields=[
        'status', 'reviewed_by', 'reviewed_at', 'review_note', 'updated_at'
    ])

    if not initiate:
        return True, 'Withdrawal approved; payout not initiated yet.'

    ok, message = initiate_payout(withdrawal)
    if ok:
        return True, message
    return True, f"Approved, but payout not sent: {message}"


@transaction.atomic
def reject_withdrawal(withdrawal: WithdrawalRequest, admin_user, note: str = ''):
    """Reject a pending withdrawal and restore reserved wallet funds."""
    if withdrawal.status in ('completed', 'rejected'):
        return False, f"Cannot reject a {withdrawal.status} withdrawal."

    txn = withdrawal.wallet_transaction
    if txn.status == 'pending':
        # Avoid double-refund if a failure credit already exists.
        already_refunded = WalletTransaction.objects.filter(
            user=withdrawal.user,
            reason='refund',
            reference__startswith=withdrawal.withdrawal_reference,
            status='completed',
        ).exists()
        if not already_refunded:
            wallet_service.credit_wallet(
                withdrawal.user,
                withdrawal.amount,
                'refund',
                reference=f"{withdrawal.withdrawal_reference}-rejected"
            )
        txn.status = 'failed'
        txn.save(update_fields=['status'])

    withdrawal.status = 'rejected'
    withdrawal.reviewed_by = admin_user
    withdrawal.reviewed_at = timezone.now()
    withdrawal.review_note = (note or 'Rejected by admin')[:2000]
    withdrawal.last_error = ''
    withdrawal.save(update_fields=[
        'status', 'reviewed_by', 'reviewed_at', 'review_note', 'last_error', 'updated_at'
    ])

    Notification.objects.create(
        user=withdrawal.user,
        title='Withdrawal Rejected',
        message=f'Your withdrawal of ₹{withdrawal.amount} was rejected. Funds restored to wallet.',
        link='/accounts/wallet/'
    )
    return True, 'Withdrawal rejected and funds restored.'


def retry_withdrawal_payout(withdrawal: WithdrawalRequest, admin_user=None):
    """Retry payout for failed/approved withdrawals while funds remain reserved."""
    if withdrawal.status not in ('failed', 'approved', 'payout_pending', 'pending_review'):
        return False, f"Cannot retry payout for status {withdrawal.status}."

    txn = withdrawal.wallet_transaction
    if txn.status == 'failed':
        # Funds were restored earlier; re-reserve before retry.
        success, new_txn, message = wallet_service.create_pending_debit(
            withdrawal.user,
            withdrawal.amount,
            'withdrawal',
            reference=withdrawal.withdrawal_reference,
        )
        if not success:
            return False, message
        withdrawal.wallet_transaction = new_txn
        withdrawal.status = 'approved'
        if admin_user:
            withdrawal.reviewed_by = admin_user
            withdrawal.reviewed_at = timezone.now()
        withdrawal.save(update_fields=[
            'wallet_transaction', 'status', 'reviewed_by', 'reviewed_at', 'updated_at'
        ])
    elif withdrawal.status in ('pending_review', 'failed'):
        withdrawal.status = 'approved'
        if admin_user:
            withdrawal.reviewed_by = admin_user
            withdrawal.reviewed_at = timezone.now()
        withdrawal.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

    return initiate_payout(withdrawal)


def mark_bank_verified(bank_account, admin_user, note: str = ''):
    bank_account.is_verified = True
    bank_account.verified_at = timezone.now()
    bank_account.verified_by = admin_user
    bank_account.verification_note = (note or 'Verified by admin')[:255]
    bank_account.save(update_fields=[
        'is_verified', 'verified_at', 'verified_by', 'verification_note', 'updated_at'
    ])
    return True, 'Bank account marked verified.'


def mark_bank_unverified(bank_account, admin_user, note: str = ''):
    bank_account.is_verified = False
    bank_account.verified_at = None
    bank_account.verified_by = admin_user
    bank_account.verification_note = (note or 'Verification revoked')[:255]
    bank_account.save(update_fields=[
        'is_verified', 'verified_at', 'verified_by', 'verification_note', 'updated_at'
    ])
    return True, 'Bank account marked unverified.'


def sync_withdrawal_from_payout_event(txn: WalletTransaction, status: str, payout_id=None):
    """Keep WithdrawalRequest in sync with Razorpay payout webhook outcomes."""
    withdrawal = getattr(txn, 'withdrawal_request', None)
    if not withdrawal:
        return

    updates = ['updated_at']
    if payout_id and withdrawal.razorpay_payout_id != payout_id:
        withdrawal.razorpay_payout_id = payout_id
        updates.append('razorpay_payout_id')

    if status in ['processed', 'paid', 'successful', 'completed', 'paid_out']:
        withdrawal.status = 'completed'
        withdrawal.last_error = ''
        updates.extend(['status', 'last_error'])
    elif status in ['failed', 'reversed', 'rejected']:
        withdrawal.status = 'failed'
        updates.append('status')

    withdrawal.save(update_fields=list(dict.fromkeys(updates)))
