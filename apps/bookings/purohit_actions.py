"""Purohit booking lifecycle actions shared by the website and /api/v1/."""

from django.utils import timezone

from apps.bookings.utils import record_booking_history


def _is_listing_purohit(user, booking):
    try:
        listing = user.purohit_profile.purohit_listing
    except Exception:
        return False
    return listing.id == booking.purohit_id


def apply_purohit_booking_status(*, booking, actor, status, verification_code=''):
    """
    Return (ok, code, message).

    Codes: confirmed, started, completed, unpaid, bad_start_code, bad_complete_code,
    forbidden, invalid.
    """
    if not _is_listing_purohit(actor, booking) and not getattr(actor, 'is_staff', False):
        return False, 'forbidden', "You don't have permission to update this booking."

    new_status = (status or '').strip()
    entered = (verification_code or '').strip()

    if new_status == 'confirmed' and not booking.accepted_at and booking.status not in ('cancelled', 'completed'):
        if booking.payment_status != 'success':
            return False, 'unpaid', 'Cannot confirm — customer payment is still pending.'
        booking.accepted_at = timezone.now()
        booking.status = 'confirmed'
        booking.save(update_fields=['status', 'accepted_at', 'updated_at'])
        record_booking_history(
            booking=booking,
            event='status_change',
            user=actor,
            message=f'Booking confirmed by purohit {actor.username}',
            old_value='pending',
            new_value='confirmed',
        )
        return True, 'confirmed', 'Booking confirmed successfully!'

    if new_status == 'confirmed' and booking.accepted_at:
        if entered != booking.start_code:
            return False, 'bad_start_code', 'Invalid Start Code! Please ask the devotee for the correct code.'
        booking.started_at = timezone.now()
        booking.save(update_fields=['started_at', 'updated_at'])
        record_booking_history(
            booking=booking,
            event='ritual_started',
            user=actor,
            message=f'Ritual started by purohit {actor.username} (Start Code: {entered})',
            old_value='confirmed',
            new_value='started',
        )
        from apps.core.notification_service import create_and_send_notification
        puja_name = booking.puja_package.puja.name if booking.puja_package_id else 'your ritual'
        create_and_send_notification(
            booking.customer,
            title='Ritual started',
            message=f'{booking.purohit.name} has started {puja_name}. Share the done code when it finishes.',
            link='/dashboard/customer/',
        )
        return True, 'started', 'Start Code Verified! Ritual has officially begun.'

    if new_status == 'completed':
        if entered != booking.complete_code:
            return False, 'bad_complete_code', 'Invalid Completion Code! Please ask the devotee for the final code.'
        booking.completed_at = timezone.now()
        booking.status = 'completed'
        booking.save(update_fields=['status', 'completed_at', 'updated_at'])
        record_booking_history(
            booking=booking,
            event='ritual_completed',
            user=actor,
            message=f'Ritual completed by purohit {actor.username} (Complete Code: {entered})',
            old_value='started',
            new_value='completed',
        )
        from apps.core.notification_service import create_and_send_notification
        puja_name = booking.puja_package.puja.name if booking.puja_package_id else 'your ritual'
        create_and_send_notification(
            booking.customer,
            title='Please review your ritual',
            message=(
                f'{booking.purohit.name} has completed {puja_name}. '
                'Please share a short review of your experience.'
            ),
            link='/dashboard/customer/#my-bookings',
        )
        return True, 'completed', 'Completion Code Verified! Ritual marked as performed.'

    return False, 'invalid', 'Invalid status transition.'
