from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
import re
import json
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

from .models import CustomUser, OTP, PurohitProfile, CustomerProfile, WalletTransaction
from .utils import send_otp_sms

# Phone number validation
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

def validate_phone_number(phone):
    """Validate and format phone number"""
    if not phone:
        raise ValidationError("Phone number is required")
    
    # Remove all non-digit characters except +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Ensure it starts with +91 for India if not already
    if phone.startswith('91') and not phone.startswith('+91'):
        phone = f'+{phone}'
    elif not phone.startswith('+'):
        phone = f'+91{phone}'
    
    # Validate format
    phone_validator(phone)
    return phone

def send_otp_view(request):
    """Send OTP to phone number"""
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        action = request.POST.get('action', 'login')  # login, signup, verify
        
        try:
            phone = validate_phone_number(phone)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('accounts:signup' if action == 'signup' else 'accounts:login')
        
        # Check if user exists for login/signup logic
        user_exists = CustomUser.objects.filter(phone=phone).exists()
        
        if action == 'signup' and user_exists:
            messages.error(request, "Phone number already registered. Please login instead.")
            return redirect('accounts:login')
        elif action == 'login' and not user_exists:
            messages.error(request, "Phone number not found. Please sign up first.")
            return redirect('accounts:signup')
        
        # Generate and send OTP
        otp_type = 'signup' if action == 'signup' else 'login'
        wait = OTP.seconds_until_resend(phone, otp_type)
        if wait > 0:
            messages.error(request, f'Wait {wait} seconds before requesting another OTP.')
            return redirect('accounts:otp_verification' if request.session.get('otp_phone') else (
                'accounts:signup' if action == 'signup' else 'accounts:login'
            ))
        otp_obj = OTP.generate_otp(phone, otp_type)
        
        success, message, sid = send_otp_sms(phone, otp_obj.otp_code, otp_type)
        
        if success:
            # Store phone in session for verification
            request.session['otp_phone'] = phone
            request.session['otp_action'] = action
            if action == 'signup':
                request.session['signup_role'] = request.POST.get('role', 'customer') or 'customer'
                request.session['signup_username'] = (request.POST.get('username') or '').strip()
                request.session['signup_email'] = (request.POST.get('email') or '').strip()
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                request.session['auth_next'] = next_url

            is_mock = str(sid or '').startswith('mock_')
            if is_mock:
                messages.success(
                    request,
                    f"OTP generated for {phone}. SMS is in mock mode — use the code shown on the next screen."
                )
            else:
                messages.success(request, f"OTP sent to {phone}")
            return redirect('accounts:otp_verification')

        messages.error(request, f"Failed to send OTP: {message}")
        return redirect('accounts:signup' if action == 'signup' else 'accounts:login')
    
    return redirect('accounts:login')

def _safe_auth_next(request):
    """Return a safe relative next URL stored during login, if any."""
    next_url = request.session.pop('auth_next', None) or request.POST.get('next') or request.GET.get('next')
    if next_url and isinstance(next_url, str) and next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return None

def verify_otp_view(request):
    """Verify OTP and complete authentication"""
    if request.method == 'POST':
        otp_code = request.POST.get('otp', '').strip()
        phone = request.session.get('otp_phone')
        action = request.session.get('otp_action')
        
        if not phone or not action:
            messages.error(request, "Session expired. Please try again.")
            return redirect('accounts:login')
        
        # Verify OTP
        success, message = OTP.verify_otp(phone, otp_code, action)
        
        if not success:
            messages.error(request, message)
            return redirect('accounts:otp_verification')
        
        # OTP verified successfully
        try:
            user = CustomUser.objects.get(phone=phone)
            # Login existing user
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            
        except CustomUser.DoesNotExist:
            # Create new user for signup
            if action == 'signup':
                username = (
                    request.POST.get('username', '').strip()
                    or request.session.get('signup_username', '').strip()
                )
                email = (
                    request.POST.get('email', '').strip()
                    or request.session.get('signup_email', '').strip()
                )
                role = (
                    request.POST.get('role')
                    or request.session.get('signup_role')
                    or 'customer'
                )
                if role not in ('customer', 'purohit'):
                    role = 'customer'
                
                if not username:
                    username = f"user_{phone.replace('+', '')}"
                
                # Create user
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email if email else None,
                    phone=phone,
                    role=role,
                    is_phone_verified=True
                )
                
                CustomerProfile.objects.get_or_create(user=user)
                if role == 'purohit':
                    PurohitProfile.objects.get_or_create(user=user)
                    from apps.purohits.services import ensure_purohit_listing
                    ensure_purohit_listing(user)
                
                login(request, user)
                from apps.accounts.workspace import set_active_workspace
                set_active_workspace(request, 'purohit' if role == 'purohit' else 'devotee')
                messages.success(request, f"Welcome to PurohitConnect, {user.get_full_name() or user.username}!")
            else:
                messages.error(request, "User not found. Please sign up first.")
                return redirect('accounts:signup')
        
        # Clear session
        request.session.pop('otp_phone', None)
        request.session.pop('otp_action', None)
        request.session.pop('signup_role', None)
        request.session.pop('signup_username', None)
        request.session.pop('signup_email', None)

        next_url = _safe_auth_next(request)
        if next_url:
            return redirect(next_url)

        from apps.accounts.workspace import set_active_workspace, workspace_home_name
        set_active_workspace(request, 'purohit' if user.role == 'purohit' else 'devotee')
        return redirect(workspace_home_name(request))
    
    return redirect('accounts:login')

def login_view(request):
    """Phone number input for login"""
    next_url = request.GET.get('next')
    if next_url and isinstance(next_url, str) and next_url.startswith('/') and not next_url.startswith('//'):
        request.session['auth_next'] = next_url
    else:
        next_url = request.session.get('auth_next', '')

    if request.user.is_authenticated:
        safe_next = _safe_auth_next(request)
        if safe_next:
            return redirect(safe_next)
        from apps.accounts.workspace import workspace_home_name
        return redirect(workspace_home_name(request))
    
    return render(request, 'accounts/login.html', {'next': next_url or ''})

def signup_view(request):
    """Phone number input for signup"""
    if request.user.is_authenticated:
        from apps.accounts.workspace import workspace_home_name
        return redirect(workspace_home_name(request))
    
    return render(request, 'accounts/signup.html')


@login_required
@require_http_methods(['GET', 'POST'])
def switch_workspace(request):
    """Flip between devotee and purohit workspaces on the same account."""
    from apps.accounts.workspace import (
        DEVOTEE,
        PUROHIT,
        can_act_as_purohit,
        enable_purohit_workspace,
        ensure_devotee_profile,
        set_active_workspace,
    )

    workspace = (
        request.POST.get('workspace') or request.GET.get('workspace') or ''
    ).strip()
    if workspace == PUROHIT:
        if not can_act_as_purohit(request.user):
            listing = enable_purohit_workspace(request.user)
            if listing is None:
                messages.error(
                    request,
                    "Purohit workspace could not be created yet. Please contact support or ensure cities are seeded.",
                )
                return redirect('dashboard:customer')
            messages.success(request, "Purohit workspace is ready. Offerings and calendar live here.")
        set_active_workspace(request, PUROHIT)
        return redirect('dashboard:purohit')

    ensure_devotee_profile(request.user)
    set_active_workspace(request, DEVOTEE)
    request.session.modified = True
    # Always land on the devotee home. Following the previous URL (often
    # /dashboard/purohit/) would immediately flip the workspace back.
    return redirect('dashboard:customer')

def otp_verification_view(request):
    """OTP input form"""
    phone = request.session.get('otp_phone')
    action = request.session.get('otp_action')
    
    if not phone or not action:
        messages.error(request, "Session expired. Please start over.")
        return redirect('accounts:login')

    mock_otp = None
    from apps.accounts.utils import sms_service
    # Never leak the code when DEBUG is off. Locally show it only if Twilio SMS is not live.
    if getattr(settings, 'DEBUG', False) and not sms_service.is_configured():
        latest = OTP.objects.filter(
            phone=phone,
            otp_type='signup' if action == 'signup' else 'login',
            is_used=False,
        ).order_by('-created_at').first()
        if latest and latest.is_valid():
            mock_otp = latest.otp_code
    
    context = {
        'phone': phone,
        'action': action,
        'mock_otp': mock_otp,
        'start_over_url': 'accounts:signup' if action == 'signup' else 'accounts:login',
        'resend_url': f'/accounts/send-otp/?phone={phone}&action={action}'
    }
    
    return render(request, 'accounts/otp_verification.html', context)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('core:home')

@login_required
def verify_phone_view(request):
    """Verify phone number for existing users who don't have verified phones"""
    if request.user.is_phone_verified:
        messages.info(request, "Your phone is already verified.")
        return redirect('core:home')
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        
        try:
            phone = validate_phone_number(phone)
            
            # Check if phone is already taken
            if CustomUser.objects.filter(phone=phone).exclude(id=request.user.id).exists():
                messages.error(request, "This phone number is already registered.")
                return redirect('accounts:verify_phone')
            
            # Generate OTP
            otp_obj = OTP.generate_otp(phone, 'verification')
            success, message, _ = send_otp_sms(phone, otp_obj.otp_code, 'verification')
            
            if success:
                request.session['verify_phone'] = phone
                messages.success(request, f"OTP sent to {phone}")
                return redirect('accounts:verify_phone_otp')
            else:
                messages.error(request, f"Failed to send OTP: {message}")
                
        except ValidationError as e:
            messages.error(request, str(e))
    
    return render(request, 'accounts/verify_phone.html')

@login_required
def verify_phone_otp_view(request):
    """Verify OTP for phone verification"""
    phone = request.session.get('verify_phone')
    
    if not phone:
        messages.error(request, "Session expired. Please try again.")
        return redirect('accounts:verify_phone')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp', '').strip()
        
        success, message = OTP.verify_otp(phone, otp_code, 'verification')
        
        if success:
            request.user.phone = phone
            request.user.is_phone_verified = True
            request.user.save()
            
            request.session.pop('verify_phone', None)
            messages.success(request, "Phone number verified successfully!")
            return redirect('core:home')
        else:
            messages.error(request, message)
    
    context = {
        'phone': phone,
        'resend_url': reverse('accounts:resend_otp')
    }
    
    return render(request, 'accounts/verify_phone_otp.html', context)

@require_POST
@csrf_exempt
def resend_otp_view(request):
    """Resend OTP (AJAX endpoint)"""
    phone = request.POST.get('phone')
    action = request.POST.get('action', 'login')
    
    if not phone:
        return JsonResponse({'success': False, 'message': 'Phone number required'})
    
    try:
        phone = validate_phone_number(phone)
        
        # Check rate limiting (max 3 OTPs per hour per phone)
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        recent_otps = OTP.objects.filter(
            phone=phone,
            created_at__gte=one_hour_ago
        ).count()
        
        if recent_otps >= 3:
            return JsonResponse({
                'success': False, 
                'message': 'Too many OTP requests. Please try again later.'
            })
        
        # Generate new OTP
        otp_obj = OTP.generate_otp(phone, action)
        success, message, _ = send_otp_sms(phone, otp_obj.otp_code, action)
        
        if success:
            return JsonResponse({
                'success': True, 
                'message': f'OTP sent to {phone}'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': f'Failed to send OTP: {message}'
            })
            
    except ValidationError as e:
        return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Unexpected error'})


# Wallet Views
from .utils import wallet_service, credit_wallet, debit_wallet, get_wallet_balance
from decimal import Decimal, InvalidOperation

@login_required
def wallet_dashboard(request):
    """Display user's wallet dashboard"""
    user = request.user
    
    # Get wallet statistics
    wallet_stats = wallet_service.calculate_wallet_stats(user)
    
    # Get recent transactions (last 10)
    recent_transactions = wallet_service.get_transaction_history(user, limit=10)
    
    context = {
        'wallet_balance': wallet_stats['current_balance'],
        'total_credited': wallet_stats['total_credited'],
        'total_debited': wallet_stats['total_debited'],
        'transaction_count': wallet_stats['transaction_count'],
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'accounts/wallet_dashboard.html', context)

@login_required
def wallet_topup(request):
    """Handle wallet top-up requests"""
    if request.method == 'POST':
        amount = request.POST.get('amount', '').strip()
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            # Create Razorpay order
            from .payment_service import PaymentProcessor
            order = PaymentProcessor.create_order(
                amount,
                f"wallet-topup-{request.user.id}-{timezone.now().timestamp()}",
                description=f"Wallet top-up for {request.user.get_full_name() or request.user.username}"
            )
            
            if order:
                # Store order ID in session for verification
                request.session['razorpay_order_id'] = order['id']
                request.session['wallet_topup_amount'] = str(amount)

                # Create a pending wallet transaction so webhook settlement can finalize the top-up
                from .utils import wallet_service
                wallet_service.create_pending_credit(
                    request.user,
                    amount,
                    'top_up',
                    reference=order.get('receipt', ''),
                    razorpay_order_id=order['id']
                )
                
                context = {
                    'order': order,
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                    'amount': amount,
                    'user': request.user,
                    'is_mock_payment': bool(order.get('mock')) or str(order.get('id', '')).startswith('order_mock_'),
                }
                return render(request, 'accounts/wallet_payment.html', context)
            else:
                messages.error(
                    request,
                    "Failed to initiate payment. Add Razorpay keys in .env, or keep RAZORPAY_ALLOW_MOCK=True for local testing."
                )
                
        except (ValueError, InvalidOperation):
            messages.error(request, "Please enter a valid amount")
        
        return redirect('accounts:wallet_topup')
    
    return render(request, 'accounts/wallet_topup.html')

@login_required
@require_POST
def verify_wallet_payment(request):
    """Verify Razorpay payment for wallet top-up"""
    from .payment_service import process_wallet_topup
    
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    amount = request.session.get('wallet_topup_amount')
    
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, amount]):
        messages.error(request, "Payment verification failed. Missing payment details.")
        return redirect('accounts:wallet_topup')
    
    try:
        amount = Decimal(amount)
        success, message, transaction = process_wallet_topup(
            request.user, amount, razorpay_order_id, razorpay_payment_id, razorpay_signature
        )
        
        if success:
            # Clear session
            request.session.pop('razorpay_order_id', None)
            request.session.pop('wallet_topup_amount', None)
            messages.success(request, f"Wallet topped up successfully with ₹{amount}!")
            return redirect('accounts:wallet_dashboard')
        else:
            messages.error(request, message)
            return redirect('accounts:wallet_topup')
            
    except Exception as e:
        messages.error(request, f"Payment verification error: {str(e)}")
        return redirect('accounts:wallet_topup')

@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Handle Razorpay webhook for payment notifications"""
    from .payment_service import PaymentProcessor

    try:
        payload = request.body
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')

        if not PaymentProcessor.verify_webhook_signature(payload, signature):
            logger.error("Invalid Razorpay webhook signature")
            return JsonResponse({'status': 'invalid_signature'}, status=400)

        data = json.loads(payload)
        success, target, message = PaymentProcessor.process_webhook_event(data)

        if success:
            return JsonResponse({'status': 'received', 'message': message})

        logger.warning(f"Razorpay webhook processing failed: {message}")
        return JsonResponse({'status': 'failed', 'message': message}, status=400)

    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received in Razorpay webhook")
        return JsonResponse({'status': 'invalid_payload'}, status=400)
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def wallet_transactions(request):
    """Display all wallet transactions with pagination and filters"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    user = request.user
    
    # Get filter parameters
    transaction_type = request.GET.get('type', '')
    reason = request.GET.get('reason', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Start with base queryset
    transactions = WalletTransaction.objects.filter(user=user)
    
    # Apply filters
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if reason:
        transactions = transactions.filter(reason=reason)
    
    if status:
        transactions = transactions.filter(status=status)
    
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(created_at__date__gte=date_from_obj)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(created_at__date__lte=date_to_obj)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    # Order by creation date (newest first)
    transactions = transactions.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 20)  # 20 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter choices for template
    transaction_types = WalletTransaction.TRANSACTION_TYPES
    transaction_reasons = WalletTransaction.TRANSACTION_REASONS
    status_choices = [('completed', 'Completed'), ('pending', 'Pending'), ('failed', 'Failed')]
    
    query = request.GET.copy()
    query.pop('page', None)

    context = {
        'page_obj': page_obj,
        'wallet_balance': get_wallet_balance(user),
        'transaction_types': transaction_types,
        'transaction_reasons': transaction_reasons,
        'status_choices': status_choices,
        'filter_query': query.urlencode(),
        'filters': {
            'type': transaction_type,
            'reason': reason,
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'accounts/wallet_transactions.html', context)

@require_POST
@login_required
def wallet_transfer(request):
    """Handle wallet-to-wallet transfers (for admin/purohit payouts)"""
    if request.user.role not in ['admin', 'purohit']:
        messages.error(request, "You don't have permission to transfer funds")
        return redirect('accounts:wallet_dashboard')
    
    recipient_username = request.POST.get('recipient_username', '').strip()
    amount = request.POST.get('amount', '').strip()
    reason = request.POST.get('reason', 'transfer')
    
    try:
        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Find recipient
        try:
            recipient = CustomUser.objects.get(username=recipient_username)
        except CustomUser.DoesNotExist:
            messages.error(request, "Recipient not found")
            return redirect('accounts:wallet_dashboard')
        
        # Perform transfer
        success, transactions, message = wallet_service.transfer_funds(
            request.user, recipient, amount, reason
        )
        
        if success:
            messages.success(request, f"₹{amount} transferred to {recipient_username}")
        else:
            messages.error(request, message)
            
    except (ValueError, InvalidOperation):
        messages.error(request, "Please enter a valid amount")
    
    return redirect('accounts:wallet_dashboard')

@login_required
def wallet_withdrawal(request):
    """Handle wallet withdrawal requests with admin review + RazorpayX payout."""
    from .models import PurohitBankAccount
    from .payout_service import create_withdrawal_request

    if request.user.role not in ['purohit', 'admin']:
        messages.error(request, "Only purohits can request bank withdrawals.")
        return redirect('accounts:wallet_dashboard')

    existing_account = PurohitBankAccount.objects.filter(user=request.user).first()

    if request.method == 'POST':
        amount = request.POST.get('amount', '').strip()
        account_holder_name = request.POST.get('account_holder_name', '').strip()
        account_number = request.POST.get('account_number', '').strip()
        ifsc_code = request.POST.get('ifsc_code', '').strip().upper()
        bank_name = request.POST.get('bank_name', '').strip()

        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")

            if amount < Decimal('100.00'):
                messages.error(request, "Minimum withdrawal amount is ₹100")
                return redirect('accounts:wallet_withdrawal')

            if not account_holder_name or not account_number or not ifsc_code:
                messages.error(request, "Account holder name, account number, and IFSC are required.")
                return redirect('accounts:wallet_withdrawal')

            if len(ifsc_code) != 11:
                messages.error(request, "IFSC code must be 11 characters.")
                return redirect('accounts:wallet_withdrawal')

            current_balance = Decimal(str(request.user.wallet_balance or 0))
            if current_balance < amount:
                messages.error(request, "Insufficient wallet balance for withdrawal.")
                return redirect('accounts:wallet_withdrawal')

            bank_account = PurohitBankAccount.objects.filter(user=request.user).first()
            details_changed = False
            if bank_account:
                details_changed = (
                    bank_account.account_number != account_number
                    or bank_account.ifsc_code != ifsc_code
                    or bank_account.account_holder_name != account_holder_name
                )

            bank_account, _created = PurohitBankAccount.objects.update_or_create(
                user=request.user,
                defaults={
                    'account_holder_name': account_holder_name,
                    'account_number': account_number,
                    'ifsc_code': ifsc_code,
                    'bank_name': bank_name,
                }
            )

            if details_changed:
                bank_account.razorpay_contact_id = None
                bank_account.razorpay_fund_account_id = None
                bank_account.is_verified = False
                bank_account.verified_at = None
                bank_account.verified_by = None
                bank_account.verification_note = 'Details changed; re-verification required'
                bank_account.save(update_fields=[
                    'razorpay_contact_id', 'razorpay_fund_account_id', 'is_verified',
                    'verified_at', 'verified_by', 'verification_note', 'updated_at'
                ])

            withdrawal_ref = f"wd-{request.user.id}-{int(timezone.now().timestamp())}"
            success, withdrawal, message = create_withdrawal_request(
                request.user, bank_account, amount, withdrawal_ref
            )
            if not success:
                messages.error(request, message)
                return redirect('accounts:wallet_withdrawal')

            if withdrawal and withdrawal.status == 'payout_pending':
                messages.success(request, message)
            elif bank_account.is_verified:
                messages.success(request, message)
            else:
                messages.info(
                    request,
                    f"{message} Your bank account is pending verification."
                )

            logger.info(
                "Withdrawal created user=%s amount=%s ref=%s status=%s",
                request.user.username, amount, withdrawal_ref,
                withdrawal.status if withdrawal else 'n/a'
            )

        except (ValueError, InvalidOperation):
            messages.error(request, "Please enter a valid amount")

        return redirect('accounts:wallet_dashboard')

    context = {
        'bank_account': existing_account,
        'wallet_balance': request.user.wallet_balance or 0,
    }
    return render(request, 'accounts/wallet_withdrawal.html', context)
