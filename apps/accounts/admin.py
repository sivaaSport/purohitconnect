from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    CustomUser, WalletTransaction, PurohitProfile, CustomerProfile,
    PurohitBankAccount, WithdrawalRequest
)
from .payout_service import (
    approve_withdrawal, reject_withdrawal, retry_withdrawal_payout,
    mark_bank_verified, mark_bank_unverified
)


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'wallet_balance', 'is_phone_verified', 'is_active', 'is_staff')
    list_filter = ('role', 'is_phone_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('PurohitConnect Info', {
            'fields': ('phone', 'role', 'city', 'avatar', 'is_phone_verified', 'wallet_balance')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('PurohitConnect Info', {
            'fields': ('phone', 'role', 'city', 'avatar', 'is_phone_verified')
        }),
    )


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'reason', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'reason', 'status')
    search_fields = ('user__username', 'user__email', 'reference', 'razorpay_order_id', 'razorpay_payment_id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(PurohitBankAccount)
class PurohitBankAccountAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'account_holder_name', 'bank_name', 'ifsc_code',
        'is_verified', 'verified_at', 'updated_at'
    )
    list_filter = ('is_verified', 'bank_name')
    search_fields = (
        'user__username', 'account_holder_name', 'account_number',
        'ifsc_code', 'razorpay_contact_id', 'razorpay_fund_account_id'
    )
    readonly_fields = (
        'razorpay_contact_id', 'razorpay_fund_account_id',
        'verified_at', 'verified_by', 'created_at', 'updated_at'
    )
    actions = ['action_mark_verified', 'action_mark_unverified']

    @admin.action(description='Mark selected bank accounts as verified')
    def action_mark_verified(self, request, queryset):
        for bank in queryset:
            mark_bank_verified(bank, request.user, note='Verified via admin action')
        self.message_user(request, f'Marked {queryset.count()} bank account(s) verified.', messages.SUCCESS)

    @admin.action(description='Mark selected bank accounts as unverified')
    def action_mark_unverified(self, request, queryset):
        for bank in queryset:
            mark_bank_unverified(bank, request.user, note='Unverified via admin action')
        self.message_user(request, f'Marked {queryset.count()} bank account(s) unverified.', messages.WARNING)


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = (
        'withdrawal_reference', 'user', 'amount', 'status',
        'payout_attempts', 'razorpay_payout_id', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = (
        'withdrawal_reference', 'user__username', 'razorpay_payout_id',
        'bank_account__account_number', 'bank_account__ifsc_code'
    )
    readonly_fields = (
        'user', 'bank_account', 'wallet_transaction', 'amount',
        'withdrawal_reference', 'razorpay_payout_id', 'payout_attempts',
        'last_error', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at'
    )
    actions = ['action_approve_and_payout', 'action_reject', 'action_retry_payout']

    @admin.action(description='Approve & initiate payout')
    def action_approve_and_payout(self, request, queryset):
        ok_count = 0
        for withdrawal in queryset:
            success, message = approve_withdrawal(withdrawal, request.user, initiate=True)
            if success:
                ok_count += 1
            else:
                self.message_user(request, f'{withdrawal.withdrawal_reference}: {message}', messages.ERROR)
        self.message_user(request, f'Processed approve/payout for {ok_count} request(s).', messages.SUCCESS)

    @admin.action(description='Reject & restore wallet funds')
    def action_reject(self, request, queryset):
        ok_count = 0
        for withdrawal in queryset:
            success, message = reject_withdrawal(withdrawal, request.user, note='Rejected via admin action')
            if success:
                ok_count += 1
            else:
                self.message_user(request, f'{withdrawal.withdrawal_reference}: {message}', messages.ERROR)
        self.message_user(request, f'Rejected {ok_count} withdrawal(s).', messages.WARNING)

    @admin.action(description='Retry RazorpayX payout')
    def action_retry_payout(self, request, queryset):
        ok_count = 0
        for withdrawal in queryset:
            success, message = retry_withdrawal_payout(withdrawal, admin_user=request.user)
            if success:
                ok_count += 1
            else:
                self.message_user(request, f'{withdrawal.withdrawal_reference}: {message}', messages.ERROR)
        self.message_user(request, f'Retried payout for {ok_count} request(s).', messages.SUCCESS)


@admin.register(PurohitProfile)
class PurohitProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_years', 'is_verified', 'verified_by_temple')
    list_filter = ('is_verified', 'experience_years')
    search_fields = ('user__username', 'user__email', 'user__phone', 'verified_by_temple')
    filter_horizontal = ('languages_spoken',)
    readonly_fields = ('user',)
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Professional Details', {
            'fields': ('languages_spoken', 'experience_years', 'about')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by_temple'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__phone')
    readonly_fields = ('user',)

    def created_at(self, obj):
        return obj.user.date_joined
    created_at.short_description = 'Joined Date'
