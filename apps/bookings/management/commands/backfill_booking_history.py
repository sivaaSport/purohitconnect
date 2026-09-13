"""
Management command to backfill BookingHistory for existing bookings.
This ensures all bookings have proper audit trails.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.bookings.models import Booking, BookingHistory


class Command(BaseCommand):
    help = 'Backfill BookingHistory for existing bookings without history'

    def handle(self, *args, **options):
        """Backfill BookingHistory records for bookings that lack proper history."""
        
        # Get all bookings
        all_bookings = Booking.objects.all()
        backfilled_count = 0
        skipped_count = 0
        
        for booking in all_bookings:
            # Check if booking already has history
            has_history = booking.history.exists()
            
            if has_history:
                skipped_count += 1
                continue
            
            # Create initial history entry for booking creation
            BookingHistory.objects.create(
                booking=booking,
                event='status_change',
                user=booking.customer,  # Assume customer created the booking
                message=f"Booking created for {booking.puja_package.puja.name if booking.puja_package else 'Unknown Puja'} on {booking.event_date}",
                old_value='none',
                new_value='pending',
                created_at=booking.created_at
            )
            
            # Create payment history if payment was made
            if booking.payment_status == 'success' and booking.payment_at:
                BookingHistory.objects.create(
                    booking=booking,
                    event='payment_success',
                    user=booking.customer,
                    message=f"Payment of ₹{booking.total_amount} completed successfully",
                    old_value='pending',
                    new_value='success',
                    created_at=booking.payment_at
                )
            
            # Create acceptance history if accepted
            if booking.accepted_at:
                BookingHistory.objects.create(
                    booking=booking,
                    event='status_change',
                    user=booking.purohit.profile.user,
                    message=f"Booking confirmed by purohit {booking.purohit.name}",
                    old_value='pending',
                    new_value='confirmed',
                    created_at=booking.accepted_at
                )
            
            # Create ritual started history if started
            if booking.started_at:
                BookingHistory.objects.create(
                    booking=booking,
                    event='ritual_started',
                    user=booking.purohit.profile.user,
                    message=f"Ritual started with code verification",
                    old_value='confirmed',
                    new_value='started',
                    created_at=booking.started_at
                )
            
            # Create completion history if completed
            if booking.completed_at:
                BookingHistory.objects.create(
                    booking=booking,
                    event='ritual_completed',
                    user=booking.purohit.profile.user,
                    message=f"Ritual completed successfully",
                    old_value='started',
                    new_value='completed',
                    created_at=booking.completed_at
                )
            
            # Create cancellation history if cancelled
            if booking.status == 'cancelled' and booking.cancellation_reason:
                BookingHistory.objects.create(
                    booking=booking,
                    event='cancellation',
                    user=booking.customer if booking.cancellation_reason.startswith('Customer') else booking.purohit.profile.user,
                    message=f"Booking cancelled: {booking.cancellation_reason}",
                    old_value=booking.status,
                    new_value='cancelled'
                )
            
            backfilled_count += 1
            self.stdout.write(
                self.style.SUCCESS(f"✓ Backfilled history for booking {booking.booking_id}")
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary:\n"
                f"  - Backfilled: {backfilled_count} bookings\n"
                f"  - Skipped (already have history): {skipped_count} bookings"
            )
        )
