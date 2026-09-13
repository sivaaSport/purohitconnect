"""Availability and time-slot helpers for purohit scheduling."""
from __future__ import annotations

from calendar import Calendar
from datetime import date, datetime, time, timedelta

from apps.bookings.models import Booking
from apps.purohits.models import PurohitAvailability

WORK_START = time(6, 0)
WORK_END = time(21, 0)
SLOT_STEP = timedelta(hours=1)
DEFAULT_DURATION_HOURS = 2.0
DEFAULT_BUFFER_MINUTES = 30

PRESETS = {
    'fullday': (None, None, 'Full day unavailable'),
    'morning': (time(6, 0), time(12, 0), 'Morning blocked'),
    'afternoon': (time(12, 0), time(17, 0), 'Afternoon blocked'),
    'evening': (time(17, 0), time(21, 0), 'Evening blocked'),
}


def _as_float_hours(value, default=DEFAULT_DURATION_HOURS) -> float:
    try:
        if value is None or value == '':
            return default
        hours = float(value)
        return hours if hours > 0 else default
    except (TypeError, ValueError):
        return default


def _as_buffer_minutes(value, default=DEFAULT_BUFFER_MINUTES) -> int:
    try:
        if value is None or value == '':
            return default
        minutes = int(value)
        return minutes if minutes >= 0 else default
    except (TypeError, ValueError):
        return default


def _parse_time(value):
    if value is None or value == '':
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    text = str(value).strip()
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def _add_hours(t: time, hours: float) -> time:
    dt = datetime.combine(date.today(), t) + timedelta(hours=hours)
    return dt.time()


def _buffered_end(end: time, buffer_minutes: int = DEFAULT_BUFFER_MINUTES) -> time:
    """End of reserved window plus soft overrun buffer (same calendar day)."""
    end_dt = datetime.combine(date.today(), end) + timedelta(minutes=_as_buffer_minutes(buffer_minutes))
    if end_dt.date() > date.today():
        return time(23, 59, 59)
    return end_dt.time()


def _overlaps(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return start_a < end_b and end_a > start_b


def work_window_for(purohit=None):
    if purohit is not None and hasattr(purohit, 'get_work_window'):
        return purohit.get_work_window()
    return WORK_START, WORK_END


def booking_buffer_minutes(booking) -> int:
    if hasattr(booking, 'get_buffer_minutes'):
        return booking.get_buffer_minutes()
    package = getattr(booking, 'puja_package', None)
    if package is not None and hasattr(package, 'get_buffer_minutes'):
        return package.get_buffer_minutes()
    return DEFAULT_BUFFER_MINUTES


def window_for(start: time | None, duration_hours: float = DEFAULT_DURATION_HOURS):
    start = start or time(9, 0)
    end = _add_hours(start, duration_hours)
    if end <= start:
        end = time(23, 59, 59)
    return start, end


def block_overlaps_window(block: PurohitAvailability, start: time, end: time) -> bool:
    if block.is_available:
        return False
    if block.is_all_day:
        return True
    b_start = block.start_time or time.min
    b_end = block.end_time or time.max
    return _overlaps(start, end, b_start, b_end)


def active_bookings_for_day(purohit, day: date):
    return Booking.objects.filter(
        purohit=purohit,
        event_date=day,
        status__in=['pending', 'confirmed'],
    ).exclude(status='cancelled').select_related('puja_package', 'puja_package__puja')


def blocks_for_day(purohit, day: date):
    return list(
        PurohitAvailability.objects.filter(purohit=purohit, date=day, is_available=False).order_by('start_time')
    )


def check_purohit_availability(
    purohit,
    date_obj,
    time_obj=None,
    duration_hours=DEFAULT_DURATION_HOURS,
    buffer_minutes=DEFAULT_BUFFER_MINUTES,
):
    """
    Check if a purohit can take a ritual on date_obj starting at time_obj.
    Duration/buffer should come from the purohit's package for new bookings.
    """
    duration_hours = _as_float_hours(duration_hours)
    buffer_minutes = _as_buffer_minutes(buffer_minutes)
    blocks = blocks_for_day(purohit, date_obj)
    work_start, work_end = work_window_for(purohit)

    if time_obj is None:
        all_day = next((b for b in blocks if b.is_all_day), None)
        if all_day:
            return False, all_day.blocked_reason or "Purohit is unavailable on this date."
        if active_bookings_for_day(purohit, date_obj).exists():
            return False, "Already booked for another ritual on this date."
        return True, "Available"

    start, end = window_for(time_obj, duration_hours)

    if start < work_start or end > work_end:
        return False, (
            f"That window is outside this purohit's working hours "
            f"({work_start.strftime('%H:%M')}–{work_end.strftime('%H:%M')})."
        )

    for block in blocks:
        if block_overlaps_window(block, start, end):
            return False, block.blocked_reason or f"Unavailable during {block.label()}."

    for booking in active_bookings_for_day(purohit, date_obj):
        b_duration = booking.get_duration_hours()
        b_start, b_end = window_for(booking.event_time, b_duration)
        if _overlaps(start, end, b_start, _buffered_end(b_end, booking_buffer_minutes(booking))):
            return False, "That time overlaps another booking (including ritual buffer)."

    return True, "Available"


def generate_slot_starts(
    duration_hours: float = DEFAULT_DURATION_HOURS,
    work_start: time | None = None,
    work_end: time | None = None,
):
    duration_hours = _as_float_hours(duration_hours)
    work_start = work_start or WORK_START
    work_end = work_end or WORK_END
    slots = []
    cursor = datetime.combine(date.today(), work_start)
    day_end = datetime.combine(date.today(), work_end)
    while cursor + timedelta(hours=duration_hours) <= day_end:
        slots.append(cursor.time())
        cursor += SLOT_STEP
    return slots


def get_day_slots(purohit, day: date, duration_hours: float = DEFAULT_DURATION_HOURS):
    """Return list of slot dicts for a day using the purohit's working hours."""
    duration_hours = _as_float_hours(duration_hours)
    work_start, work_end = work_window_for(purohit)
    blocks = blocks_for_day(purohit, day)
    bookings = list(active_bookings_for_day(purohit, day))
    all_day_blocked = any(b.is_all_day for b in blocks)

    slots = []
    for start in generate_slot_starts(duration_hours, work_start=work_start, work_end=work_end):
        end = _add_hours(start, duration_hours)
        status = 'available'
        reason = ''
        if all_day_blocked:
            status = 'blocked'
            reason = 'Full day blocked'
        else:
            for block in blocks:
                if block_overlaps_window(block, start, end):
                    status = 'blocked'
                    reason = block.blocked_reason or block.label()
                    break
            if status == 'available':
                for booking in bookings:
                    b_duration = booking.get_duration_hours()
                    b_start, b_end = window_for(booking.event_time, b_duration)
                    if _overlaps(start, end, b_start, _buffered_end(b_end, booking_buffer_minutes(booking))):
                        status = 'booked'
                        reason = 'Already booked'
                        break

        slots.append({
            'start': start,
            'end': end,
            'value': start.strftime('%H:%M'),
            'label': f"{start.strftime('%H:%M')} – {end.strftime('%H:%M')}",
            'status': status,
            'reason': reason,
            'available': status == 'available',
        })
    return slots


def day_status(purohit, day: date, duration_hours: float = DEFAULT_DURATION_HOURS) -> str:
    """Return free | partial | full | past for calendar coloring."""
    from django.utils import timezone
    today = timezone.localdate()
    if day < today:
        return 'past'
    slots = get_day_slots(purohit, day, duration_hours)
    if not slots:
        return 'full'
    available = sum(1 for s in slots if s['available'])
    if available == 0:
        return 'full'
    if available == len(slots):
        return 'free'
    return 'partial'


def build_month_calendar(purohit, year: int, month: int, duration_hours: float = DEFAULT_DURATION_HOURS, today=None):
    from django.utils import timezone
    today = today or timezone.localdate()
    weeks = []
    for week in Calendar(firstweekday=0).monthdatescalendar(year, month):
        row = []
        for day in week:
            in_month = day.month == month
            status = day_status(purohit, day, duration_hours) if in_month else 'outside'
            blocks = blocks_for_day(purohit, day) if in_month else []
            row.append({
                'date': day,
                'in_month': in_month,
                'is_today': day == today,
                'is_past': day < today,
                'status': status,
                'is_blocked': status == 'full',
                'is_partial': status == 'partial',
                'blocks': blocks,
                'block_count': len(blocks),
                'blocked_reason': blocks[0].blocked_reason if blocks else '',
            })
        weeks.append(row)
    return weeks


def add_block(purohit, day: date, start_time=None, end_time=None, reason=''):
    start_time = _parse_time(start_time)
    end_time = _parse_time(end_time)
    if (start_time is None) != (end_time is None):
        raise ValueError("Provide both start and end time, or leave both empty for a full-day block.")
    if start_time and end_time and start_time >= end_time:
        raise ValueError("End time must be after start time.")

    if start_time is None and end_time is None:
        PurohitAvailability.objects.filter(purohit=purohit, date=day).delete()
        return PurohitAvailability.objects.create(
            purohit=purohit,
            date=day,
            start_time=None,
            end_time=None,
            is_available=False,
            blocked_reason=(reason or 'Unavailable')[:200],
        )

    PurohitAvailability.objects.filter(
        purohit=purohit, date=day, start_time__isnull=True, end_time__isnull=True
    ).delete()

    return PurohitAvailability.objects.create(
        purohit=purohit,
        date=day,
        start_time=start_time,
        end_time=end_time,
        is_available=False,
        blocked_reason=(reason or 'Blocked')[:200],
    )


def clear_day_blocks(purohit, day: date):
    deleted, _ = PurohitAvailability.objects.filter(purohit=purohit, date=day).delete()
    return deleted


def apply_preset(purohit, day: date, preset: str):
    if preset not in PRESETS:
        raise ValueError("Unknown preset.")
    start, end, reason = PRESETS[preset]
    if preset == 'fullday':
        return add_block(purohit, day, None, None, reason)
    return add_block(purohit, day, start, end, reason)
