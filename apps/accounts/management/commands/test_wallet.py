from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.accounts.utils import wallet_service

User = get_user_model()

class Command(BaseCommand):
    help = 'Test wallet functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing Wallet Functionality...\n')

        # Get or create test users
        try:
            user1 = User.objects.get(username='testuser1')
        except User.DoesNotExist:
            user1 = User.objects.create_user(
                username='testuser1',
                email='test1@example.com',
                password='testpass123',
                role='customer'
            )

        try:
            user2 = User.objects.get(username='testuser2')
        except User.DoesNotExist:
            user2 = User.objects.create_user(
                username='testuser2',
                email='test2@example.com',
                password='testpass123',
                role='customer'
            )

        self.stdout.write(f'User 1: {user1.username} (Balance: ₹{user1.wallet_balance})')
        self.stdout.write(f'User 2: {user2.username} (Balance: ₹{user2.wallet_balance})')

        # Test credit operation
        self.stdout.write('\n--- Testing Credit Operation ---')
        success, transaction, message = wallet_service.credit_wallet(
            user1, Decimal('500.00'), 'top_up', 'Test top-up'
        )
        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ Credit successful: {message}'))
            self.stdout.write(f'User 1 balance: ₹{user1.wallet_balance}')
        else:
            self.stdout.write(self.style.ERROR(f'✗ Credit failed: {message}'))

        # Test debit operation
        self.stdout.write('\n--- Testing Debit Operation ---')
        success, transaction, message = wallet_service.debit_wallet(
            user1, Decimal('200.00'), 'booking_payment', 'Test booking'
        )
        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ Debit successful: {message}'))
            self.stdout.write(f'User 1 balance: ₹{user1.wallet_balance}')
        else:
            self.stdout.write(self.style.ERROR(f'✗ Debit failed: {message}'))

        # Test transfer operation
        self.stdout.write('\n--- Testing Transfer Operation ---')
        success, transactions, message = wallet_service.transfer_funds(
            user1, user2, Decimal('100.00'), 'transfer', 'Test transfer'
        )
        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ Transfer successful: {message}'))
            user1.refresh_from_db()
            user2.refresh_from_db()
            self.stdout.write(f'User 1 balance: ₹{user1.wallet_balance}')
            self.stdout.write(f'User 2 balance: ₹{user2.wallet_balance}')
        else:
            self.stdout.write(self.style.ERROR(f'✗ Transfer failed: {message}'))

        # Test insufficient balance
        self.stdout.write('\n--- Testing Insufficient Balance ---')
        success, transaction, message = wallet_service.debit_wallet(
            user1, Decimal('1000.00'), 'booking_payment', 'Test booking'
        )
        if not success:
            self.stdout.write(self.style.SUCCESS(f'✓ Insufficient balance check: {message}'))
        else:
            self.stdout.write(self.style.ERROR('✗ Should have failed due to insufficient balance'))

        # Show transaction history
        self.stdout.write('\n--- Transaction History ---')
        transactions = wallet_service.get_transaction_history(user1, limit=10)
        for txn in transactions:
            self.stdout.write(f'{txn.created_at}: {txn.transaction_type} ₹{txn.amount} ({txn.reason}) - {txn.status}')

        # Show wallet stats
        self.stdout.write('\n--- Wallet Statistics ---')
        stats = wallet_service.calculate_wallet_stats(user1)
        self.stdout.write(f'Current Balance: ₹{stats["current_balance"]}')
        self.stdout.write(f'Total Credited: ₹{stats["total_credited"]}')
        self.stdout.write(f'Total Debited: ₹{stats["total_debited"]}')
        self.stdout.write(f'Transaction Count: {stats["transaction_count"]}')

        self.stdout.write('\n' + self.style.SUCCESS('Wallet functionality test completed!'))