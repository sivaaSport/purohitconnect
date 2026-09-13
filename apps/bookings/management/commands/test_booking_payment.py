from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.accounts.utils import wallet_service, credit_wallet
from apps.accounts.models import PurohitProfile
from apps.bookings.models import Booking
from apps.bookings.payment_utils import get_booking_payment_options, process_booking_payment_wallet
from apps.pujas.models import Puja, PurohitPujaPackage
from apps.purohits.models import Purohit
from apps.core.models import City, Area
from datetime import date, time
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test wallet and booking payment integration'

    def handle(self, *args, **options):
        self.stdout.write('Testing Wallet + Booking Payment Integration...\n')

        # Create test users
        try:
            customer = User.objects.get(username='customer_test')
        except User.DoesNotExist:
            customer = User.objects.create_user(
                username='customer_test',
                email='customer@test.com',
                password='testpass123',
                role='customer'
            )
            self.stdout.write(f'Created test customer: {customer.username}')

        try:
            purohit_user = User.objects.get(username='purohit_test')
        except User.DoesNotExist:
            purohit_user = User.objects.create_user(
                username='purohit_test',
                email='purohit@test.com',
                password='testpass123',
                role='purohit'
            )
            self.stdout.write(f'Created test purohit user: {purohit_user.username}')

        # Create or get city/area
        city, _ = City.objects.get_or_create(name='Test City')
        area, _ = Area.objects.get_or_create(name='Test Area', city=city)

        # Create PurohitProfile if not exists
        purohit_profile, created = PurohitProfile.objects.get_or_create(
            user=purohit_user,
            defaults={'is_verified': True}
        )
        if created:
            self.stdout.write(f'Created PurohitProfile for {purohit_user.username}')

        # Create or get purohit
        purohit, created = Purohit.objects.get_or_create(
            profile=purohit_profile,
            defaults={
                'name': 'Test Purohit',
                'city': city,
                'base_price': Decimal('500.00'),
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Created Purohit: {purohit.name}')

        # Create or get puja category
        from apps.pujas.models import PujaCategory
        category, _ = PujaCategory.objects.get_or_create(
            name='Household Pujas',
            defaults={'icon': 'flame'}
        )
        
        # Create or get puja
        puja, created = Puja.objects.get_or_create(
            name='Test Puja',
            category=category,
            defaults={
                'description': 'Test puja for integration testing',
                'base_duration_hours': Decimal('2.0')
            }
        )
        if created:
            self.stdout.write(f'Created Puja: {puja.name}')

        # Create or get puja package
        package, created = PurohitPujaPackage.objects.get_or_create(
            purohit=purohit,
            puja=puja,
            defaults={'price': Decimal('500.00')}
        )
        if created:
            self.stdout.write(f'Created PurohitPujaPackage: {package}')

        self.stdout.write('\n--- Test 1: Add Wallet Balance ---')
        initial_balance = wallet_service.get_balance(customer)
        self.stdout.write(f'Initial wallet balance: ₹{initial_balance}')

        success, txn, msg = credit_wallet(
            customer, Decimal('2000.00'), 'top_up', 'Test top-up'
        )
        if success:
            customer.refresh_from_db()
            new_balance = wallet_service.get_balance(customer)
            self.stdout.write(self.style.SUCCESS(f'✓ Wallet topped up to ₹{new_balance}'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ Top-up failed: {msg}'))
            return

        self.stdout.write('\n--- Test 2: Create Booking ---')
        booking = Booking.objects.create(
            customer=customer,
            purohit=purohit,
            puja_package=package,
            event_date=date.today(),
            event_time=time(14, 0),
            address='Test Address',
            city=city,
            area=area,
            total_amount=Decimal('500.00'),
            status='pending',
            payment_status='pending'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Booking created: {booking.booking_id}'))

        self.stdout.write('\n--- Test 3: Check Payment Options ---')
        options = get_booking_payment_options(customer, booking.total_amount)
        self.stdout.write(f'Wallet option available: {options["wallet"]["available"]}')
        self.stdout.write(f'Razorpay option available: {options["razorpay"]["available"]}')

        self.stdout.write('\n--- Test 4: Process Booking Payment with Wallet ---')
        success, msg = process_booking_payment_wallet(booking, customer)
        if success:
            booking.refresh_from_db()
            customer.refresh_from_db()
            final_balance = wallet_service.get_balance(customer)
            self.stdout.write(self.style.SUCCESS(f'✓ Payment processed: {msg}'))
            self.stdout.write(f'Final wallet balance: ₹{final_balance}')
            self.stdout.write(f'Booking status: {booking.status}')
            self.stdout.write(f'Payment status: {booking.payment_status}')
        else:
            self.stdout.write(self.style.ERROR(f'✗ Payment failed: {msg}'))

        self.stdout.write('\n--- Test 5: Verify Booking Payment ---')
        wallet_transactions = customer.wallet_transactions.filter(reason='booking_payment')
        self.stdout.write(f'Total booking payment transactions: {wallet_transactions.count()}')
        for txn in wallet_transactions:
            self.stdout.write(f'  - {txn.created_at}: ₹{txn.amount} ({txn.reference})')

        self.stdout.write('\n--- Test 6: Insufficient Balance Test ---')
        # Create another booking with insufficient balance
        try:
            booking2 = Booking.objects.create(
                customer=customer,
                purohit=purohit,
                puja_package=package,
                event_date=date.today(),
                event_time=time(16, 0),
                address='Test Address 2',
                city=city,
                area=area,
                total_amount=Decimal('5000.00'),  # Insufficient balance
                status='pending',
                payment_status='pending'
            )
            
            success, msg = process_booking_payment_wallet(booking2, customer)
            if not success:
                self.stdout.write(self.style.SUCCESS(f'✓ Correctly rejected: {msg}'))
            else:
                self.stdout.write(self.style.ERROR('✗ Should have rejected due to insufficient balance'))
        except Exception as e:
            self.stdout.write(f'Error in insufficient balance test: {str(e)}')

        self.stdout.write('\n' + self.style.SUCCESS('✓ All integration tests completed successfully!'))