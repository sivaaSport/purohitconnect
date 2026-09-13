"""Utility functions for booking reschedule operations."""
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import Booking, BookingHistory
from apps.purohits.utils import check_purohit_availability


def record_booking_history(booking: Booking, event: str, user, message: str, old_value: str = '', new_value: str = ''):
    """Record a booking history event."""
    return BookingHistory.objects.create(
        booking=booking,
        event=event,
        user=user,
        message=message,
        old_value=old_value,
        new_value=new_value
    )


def _parse_date(value):
    if hasattr(value, 'year'):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, '%Y-%m-%d').date()
    raise ValueError('Invalid date')


def _parse_time(value):
    if value in (None, ''):
        return None
    if hasattr(value, 'hour'):
        return value
    if isinstance(value, str):
        for fmt in ('%H:%M', '%H:%M:%S'):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
    raise ValueError('Invalid time')


def _max_reschedules():
    return int(getattr(settings, 'RESCHEDULE_MAX_COUNT', 2))


def _min_notice_hours():
    return int(getattr(settings, 'RESCHEDULE_MIN_NOTICE_HOURS', 48))


def _pending_expire_hours():
    return int(getattr(settings, 'RESCHEDULE_PENDING_EXPIRE_HOURS', 24))


def validate_reschedule_window(booking: Booking):
    """Ensure request is made early enough before the current event."""
    if not booking.event_date:
        return False, "Booking has no event date."

    try:
        event_time = _parse_time(booking.event_time) if booking.event_time else datetime.min.time()
    except ValueError:
        event_time = datetime.min.time()
    event_dt = datetime.combine(booking.event_date, event_time)
    if timezone.is_naive(event_dt):
        event_dt = timezone.make_aware(event_dt, timezone.get_current_timezone())

    hours_until = (event_dt - timezone.now()).total_seconds() / 3600.0
    min_hours = _min_notice_hours()
    if hours_until < min_hours:
        return False, f"Reschedule requests must be made at least {min_hours} hours before the ritual."
    return True, ""


def request_reschedule(booking: Booking, suggested_date, suggested_time, requested_by, reason: str = ''):
    """
    Record a reschedule request from purohit or customer.
    """
    if booking.status == 'cancelled':
        return False, "Cannot reschedule a cancelled booking."

    if booking.status == 'completed' or booking.completed_at:
        return False, "Cannot reschedule a completed ritual."

    if booking.started_at:
        return False, "Cannot reschedule after the ritual has started."

    if booking.reschedule_status == 'pending':
        return False, "A reschedule request is already pending."

    if booking.reschedule_count >= _max_reschedules():
        return False, f"Maximum of {_max_reschedules()} reschedules allowed for this booking."

    ok, message = validate_reschedule_window(booking)
    if not ok:
        return False, message

    try:
        suggested_date = _parse_date(suggested_date)
        suggested_time = _parse_time(suggested_time)
    except ValueError:
        return False, "Invalid suggested date/time."

    if suggested_date < timezone.localdate():
        return False, "Suggested date cannot be in the past."

    is_available, reason_msg = check_purohit_availability(
        booking.purohit,
        suggested_date,
        time_obj=suggested_time,
        duration_hours=booking.get_duration_hours(),
        buffer_minutes=booking.get_buffer_minutes(),
    )
    if not is_available:
        return False, f"Purohit is not available on {suggested_date}: {reason_msg}"

    old_date = str(booking.event_date)
    booking.suggested_date = suggested_date
    booking.suggested_time = suggested_time
    booking.reschedule_requested_by = requested_by
    booking.reschedule_status = 'pending'
    booking.reschedule_requested_at = timezone.now()
    booking.reschedule_accepted_at = None
    booking.reschedule_rejected_at = None
    booking.reschedule_reason = (reason or '')[:255]
    booking.save(update_fields=[
        'suggested_date', 'suggested_time', 'reschedule_requested_by',
        'reschedule_status', 'reschedule_requested_at', 'reschedule_accepted_at',
        'reschedule_rejected_at', 'reschedule_reason', 'updated_at'
    ])

    role_label = 'Customer' if getattr(requested_by, 'role', '') == 'customer' else 'Purohit'
    reason_suffix = f" Reason: {reason}" if reason else ""
    BookingHistory.objects.create(
        booking=booking,
        event='reschedule_requested',
        user=requested_by,
        message=f"{role_label} requested reschedule to {suggested_date}.{reason_suffix}",
        old_value=old_date,
        new_value=str(suggested_date)
    )

    return True, f"Reschedule request sent. Suggested date: {suggested_date}"


def accept_reschedule(booking: Booking, accepted_by):
    """Counterparty accepts a pending reschedule request."""
    if booking.reschedule_status != 'pending':
        return False, "No pending reschedule request to accept."

    if not booking.suggested_date:
        return False, "No suggested date available."

    # Only the non-requester can accept
    if booking.reschedule_requested_by_id and booking.reschedule_requested_by_id == getattr(accepted_by, 'id', None):
        return False, "You cannot accept your own reschedule request."

    is_available, reason = check_purohit_availability(
        booking.purohit,
        booking.suggested_date,
        time_obj=booking.suggested_time,
        duration_hours=booking.get_duration_hours(),
        buffer_minutes=booking.get_buffer_minutes(),
    )
    if not is_available:
        return False, f"Purohit is no longer available on {booking.suggested_date}: {reason}"

    old_date = str(booking.event_date)
    booking.event_date = booking.suggested_date
    booking.event_time = booking.suggested_time if booking.suggested_time else booking.event_time
    booking.reschedule_status = 'accepted'
    booking.reschedule_accepted_at = timezone.now()
    booking.reschedule_count += 1
    booking.suggested_date = None
    booking.suggested_time = None

    booking.save(update_fields=[
        'event_date', 'event_time', 'reschedule_status', 'reschedule_accepted_at',
        'reschedule_count', 'suggested_date', 'suggested_time', 'updated_at'
    ])

    BookingHistory.objects.create(
        booking=booking,
        event='reschedule_accepted',
        user=accepted_by,
        message=f"Reschedule accepted. New date: {booking.event_date}",
        old_value=old_date,
        new_value=str(booking.event_date)
    )

    return True, f"Reschedule accepted! Ritual rescheduled to {booking.event_date}."


def reject_reschedule(booking: Booking, rejected_by, reason: str = ''):
    """Counterparty rejects a pending reschedule request."""
    if booking.reschedule_status != 'pending':
        return False, "No pending reschedule request to reject."

    if booking.reschedule_requested_by_id and booking.reschedule_requested_by_id == getattr(rejected_by, 'id', None):
        return False, "You cannot reject your own reschedule request."

    suggested_date = booking.suggested_date
    booking.reschedule_status = 'rejected'
    booking.reschedule_rejected_at = timezone.now()
    booking.suggested_date = None
    booking.suggested_time = None
    if reason:
        booking.reschedule_reason = reason[:255]

    booking.save(update_fields=[
        'reschedule_status', 'reschedule_rejected_at', 'suggested_date',
        'suggested_time', 'reschedule_reason', 'updated_at'
    ])

    reason_suffix = f" Reason: {reason}" if reason else ""
    BookingHistory.objects.create(
        booking=booking,
        event='reschedule_rejected',
        user=rejected_by,
        message=f"Reschedule request for {suggested_date} was declined.{reason_suffix}",
        old_value=str(suggested_date),
        new_value=str(booking.event_date)
    )

    return True, "Reschedule request declined. Original date remains."


def expire_pending_reschedule(booking: Booking):
    """Auto-expire a single pending reschedule request."""
    if booking.reschedule_status != 'pending' or not booking.reschedule_requested_at:
        return False, "No pending request to expire."

    cutoff = timezone.now() - timedelta(hours=_pending_expire_hours())
    if booking.reschedule_requested_at > cutoff:
        return False, "Request has not expired yet."

    suggested_date = booking.suggested_date
    booking.reschedule_status = 'rejected'
    booking.reschedule_rejected_at = timezone.now()
    booking.suggested_date = None
    booking.suggested_time = None
    booking.save(update_fields=[
        'reschedule_status', 'reschedule_rejected_at',
        'suggested_date', 'suggested_time', 'updated_at'
    ])

    BookingHistory.objects.create(
        booking=booking,
        event='reschedule_expired',
        user=None,
        message=f"Pending reschedule to {suggested_date} expired after {_pending_expire_hours()} hours without response.",
        old_value=str(suggested_date or ''),
        new_value=str(booking.event_date)
    )
    return True, "Pending reschedule expired."


def expire_pending_reschedules(limit: int = 200):
    """Expire all pending reschedule requests older than policy window."""
    cutoff = timezone.now() - timedelta(hours=_pending_expire_hours())
    pending = Booking.objects.filter(
        reschedule_status='pending',
        reschedule_requested_at__lte=cutoff
    ).order_by('reschedule_requested_at')[:limit]

    expired = 0
    for booking in pending:
        success, _ = expire_pending_reschedule(booking)
        if success:
            expired += 1
    return expired


def reset_reschedule_request(booking: Booking, requesting_user):
    """Reset rejected/accepted status so a new request can be made."""
    if booking.status in ('cancelled', 'completed'):
        return False, "Cannot reschedule cancelled or completed bookings."

    if booking.reschedule_count >= _max_reschedules():
        return False, f"Maximum of {_max_reschedules()} reschedules already used."

    old_status = booking.reschedule_status
    booking.reschedule_status = 'none'
    booking.suggested_date = None
    booking.suggested_time = None

    booking.save(update_fields=[
        'reschedule_status', 'suggested_date', 'suggested_time', 'updated_at'
    ])

    BookingHistory.objects.create(
        booking=booking,
        event='status_change',
        user=requesting_user,
        message="Reschedule request reset. New request can be made.",
        old_value=old_status,
        new_value='none'
    )

    return True, "Ready to request a new reschedule."
