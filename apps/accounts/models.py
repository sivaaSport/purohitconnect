from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import hmac
import random
import string
from apps.core.models import City, Language

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('purohit', 'Purohit'),
        ('admin', 'Admin'),
    )
    phone = models.CharField(max_length=13, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def can_act_as_devotee(self):
        """Any signed-in person can book rituals as a devotee."""
        return True

    def can_act_as_purohit(self):
        """True once this account has (or is creating) a purohit listing."""
        if self.role == 'purohit':
            return True
        return hasattr(self, 'purohit_profile')

    def has_dual_workspace(self):
        return self.can_act_as_devotee() and self.can_act_as_purohit()

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    
    TRANSACTION_REASONS = (
        ('top_up', 'Wallet Top-up'),
        ('booking_payment', 'Booking Payment'),
        ('payout', 'Purohit Payout'),
        ('refund', 'Refund'),
        ('withdrawal', 'Bank Withdrawal'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='wallet_transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    reason = models.CharField(max_length=20, choices=TRANSACTION_REASONS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, help_text="Booking ID, Payment ID, etc.")
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, default='completed', help_text="pending, completed, failed")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['razorpay_order_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} ₹{self.amount} ({self.reason})"

class OTP(models.Model):
    OTP_TYPES = (
        ('login', 'Login'),
        ('signup', 'Signup'),
        ('verification', 'Phone Verification'),
    )
    
    phone = models.CharField(max_length=13)
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES, default='login')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    class Meta:
        indexes = [
            models.Index(fields=['phone', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.phone} ({self.otp_type})"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired() and self.attempts < self.max_attempts
    
    def increment_attempts(self):
        self.attempts += 1
        self.save()
    
    RESEND_COOLDOWN_SECONDS = 45

    @classmethod
    def seconds_until_resend(cls, phone, otp_type='login'):
        latest = (
            cls.objects.filter(phone=phone, otp_type=otp_type, is_used=False)
            .order_by('-created_at')
            .first()
        )
        if latest is None:
            return 0
        elapsed = (timezone.now() - latest.created_at).total_seconds()
        wait = cls.RESEND_COOLDOWN_SECONDS - elapsed
        return int(wait) if wait > 0 else 0

    @classmethod
    def generate_otp(cls, phone, otp_type='login'):
        cls.objects.filter(phone=phone, expires_at__lt=timezone.now()).delete()
        cls.objects.filter(phone=phone, otp_type=otp_type, is_used=False).update(is_used=True)

        otp_code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=5)
        return cls.objects.create(
            phone=phone,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at,
        )

    @classmethod
    def verify_otp(cls, phone, otp_code, otp_type='login'):
        otp = (
            cls.objects.filter(phone=phone, otp_type=otp_type, is_used=False)
            .order_by('-created_at')
            .first()
        )
        if otp is None:
            return False, "Invalid OTP"
        if otp.is_expired():
            return False, "OTP has expired"
        if otp.attempts >= otp.max_attempts:
            return False, "Maximum attempts exceeded"

        entered = (otp_code or '').strip()
        expected = (otp.otp_code or '').strip()
        code_ok = (
            len(entered) == len(expected) == 6
            and hmac.compare_digest(entered, expected)
        )
        if not code_ok:
            otp.increment_attempts()
            otp.refresh_from_db(fields=['attempts'])
            if otp.attempts >= otp.max_attempts:
                return False, "Maximum attempts exceeded"
            remaining = otp.max_attempts - otp.attempts
            return False, f"Invalid OTP. {remaining} attempts remaining"

        otp.is_used = True
        otp.save(update_fields=['is_used'])
        return True, "OTP verified successfully"

class PurohitProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='purohit_profile')
    languages_spoken = models.ManyToManyField(Language)
    experience_years = models.IntegerField(default=0)
    about = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by_temple = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return f"Purohit {self.user.get_full_name() or self.user.username}"

class CustomerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='customer_profile')
    
    def __str__(self):
        return f"Customer {self.user.get_full_name() or self.user.username}"


class PurohitBankAccount(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='bank_account')
    account_holder_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=11)
    bank_name = models.CharField(max_length=100, blank=True)
    
    # RazorpayX specific IDs
    razorpay_contact_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_fund_account_id = models.CharField(max_length=100, blank=True, null=True)
    
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_bank_accounts'
    )
    verification_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        acc_num = self.account_number[-4:] if len(self.account_number) >= 4 else self.account_number
        return f"{self.user.username} - {self.bank_name or 'Bank'} (***{acc_num})"


class WithdrawalRequest(models.Model):
    """Admin-reviewed bank withdrawal tied to a reserved wallet debit."""

    STATUS_CHOICES = (
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('payout_pending', 'Payout Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='withdrawal_requests')
    bank_account = models.ForeignKey(
        PurohitBankAccount, on_delete=models.PROTECT, related_name='withdrawal_requests'
    )
    wallet_transaction = models.OneToOneField(
        WalletTransaction, on_delete=models.CASCADE, related_name='withdrawal_request'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_review')
    withdrawal_reference = models.CharField(max_length=64, unique=True)
    razorpay_payout_id = models.CharField(max_length=100, blank=True, null=True)
    payout_attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_withdrawals'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.withdrawal_reference} ({self.status}) ₹{self.amount}"
