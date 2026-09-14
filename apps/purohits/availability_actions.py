"""Availability calendar actions shared by the website and /api/v1/."""

from datetime import datetime

from apps.purohits.models import PurohitAvailability
from apps.purohits.utils import _parse_time, add_block, apply_preset, clear_day_blocks


def apply_availability_action(*, purohit, action, data):
    """
    Return (ok, code, message, extra).

    extra may include redirect_day (YYYY-MM-DD).
    Codes: hours_saved, block_removed, day_cleared, preset_applied, range_blocked,
    day_blocked, invalid, bad_hours, bad_date.
    """
    action = (action or 'block_day').strip()
    data = data or {}
    date_str = (data.get('date') or '').strip()
    reason = (data.get('reason') or '').strip()
    extra = {'redirect_day': date_str}

    try:
        if action == 'set_work_hours':
            start = _parse_time(data.get('work_start'))
            end = _parse_time(data.get('work_end'))
            if not start or not end:
                return False, 'bad_hours', 'Provide both start and end working hours.', extra
            if end <= start:
                return False, 'bad_hours', 'Working day end must be after start.', extra
            start_mins = start.hour * 60 + start.minute
            end_mins = end.hour * 60 + end.minute
            if end_mins - start_mins < 60:
                return False, 'bad_hours', 'Working window must be at least 1 hour.', extra
            purohit.work_start = start
            purohit.work_end = end
            purohit.save(update_fields=['work_start', 'work_end', 'updated_at'])
            return (
                True,
                'hours_saved',
                (
                    f"Working hours updated to {start.strftime('%H:%M')}–{end.strftime('%H:%M')}. "
                    'Devotee slots now use this day window.'
                ),
                extra,
            )

        if action == 'delete_block':
            try:
                block = PurohitAvailability.objects.get(id=data.get('block_id'), purohit=purohit)
            except (PurohitAvailability.DoesNotExist, ValueError, TypeError):
                return False, 'invalid', 'That blocked window was not found.', extra
            extra['redirect_day'] = block.date.isoformat()
            block.delete()
            return True, 'block_removed', 'Blocked window removed.', extra

        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        if action != 'set_work_hours' and date_obj is None and action != 'delete_block':
            return False, 'bad_date', 'Pick a date first.', extra

        if action == 'clear_day':
            cleared = clear_day_blocks(purohit, date_obj)
            return True, 'day_cleared', f'Cleared {cleared} block(s) on {date_str}.', extra

        if action == 'preset':
            apply_preset(purohit, date_obj, data.get('preset') or 'fullday')
            return True, 'preset_applied', f'Applied availability preset on {date_str}.', extra

        if action == 'add_range':
            add_block(
                purohit,
                date_obj,
                data.get('start_time'),
                data.get('end_time'),
                reason or 'Blocked',
            )
            return (
                True,
                'range_blocked',
                f"Blocked {data.get('start_time')}–{data.get('end_time')} on {date_str}.",
                extra,
            )

        if action == 'block_day':
            add_block(purohit, date_obj, None, None, reason or 'Unavailable')
            return True, 'day_blocked', f'{date_str} marked unavailable all day.', extra

        return False, 'invalid', 'Unknown availability action.', extra
    except ValueError as exc:
        return False, 'invalid', str(exc), extra


def _fmt_time(value):
    return value.strftime('%H:%M') if value else ''


def calendar_cell_payload(cell):
    day = cell['date']
    return {
        'date': day.isoformat(),
        'day': day.day,
        'in_month': cell['in_month'],
        'is_today': cell['is_today'],
        'is_past': cell['is_past'],
        'status': cell['status'],
        'block_count': cell['block_count'],
    }


def availability_block_payload(block):
    return {
        'id': block.id,
        'date': block.date.isoformat() if block.date else '',
        'start_time': _fmt_time(block.start_time),
        'end_time': _fmt_time(block.end_time),
        'is_all_day': block.is_all_day,
        'label': block.label(),
        'reason': block.blocked_reason or '',
    }


def calendar_state(purohit, *, year=None, month=None, day=None, preview_package_id=None):
    from calendar import month_name
    from datetime import date
    from django.utils import timezone
    from apps.purohits.utils import (
        active_bookings_for_day,
        blocks_for_day,
        build_month_calendar,
        get_day_slots,
    )

    today = timezone.localdate()
    try:
        year = int(year or today.year)
        month = int(month or today.month)
    except (TypeError, ValueError):
        year, month = today.year, today.month
    if month < 1 or month > 12:
        year, month = today.year, today.month

    packages = list(purohit.puja_packages.select_related('puja', 'puja__category').order_by('puja__name'))
    preview = None
    if preview_package_id not in (None, ''):
        preview = next((item for item in packages if str(item.id) == str(preview_package_id)), None)
    if preview is None and packages:
        preview = max(packages, key=lambda item: item.get_duration_hours())
    duration = preview.get_duration_hours() if preview else 2.0

    weeks = build_month_calendar(purohit, year, month, duration_hours=duration, today=today)

    selected_day = None
    selected_blocks = []
    selected_bookings = []
    selected_slots = []
    day_raw = (day or '').strip() if isinstance(day, str) else day
    if day_raw:
        try:
            selected_day = date.fromisoformat(str(day_raw))
            selected_blocks = blocks_for_day(purohit, selected_day)
            selected_bookings = list(active_bookings_for_day(purohit, selected_day))
            selected_slots = get_day_slots(purohit, selected_day, duration_hours=duration)
        except ValueError:
            selected_day = None

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    return {
        'year': year,
        'month': month,
        'month_label': f'{month_name[month]} {year}',
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'work_start': _fmt_time(purohit.work_start) or '06:00',
        'work_end': _fmt_time(purohit.work_end) or '21:00',
        'calendar_duration': duration,
        'preview_package_id': preview.id if preview else None,
        'weeks': [[calendar_cell_payload(cell) for cell in week] for week in weeks],
        'selected_day': selected_day.isoformat() if selected_day else '',
        'selected_blocks': [availability_block_payload(block) for block in selected_blocks],
        'selected_bookings': [
            {
                'booking_id': booking.booking_id,
                'puja_name': booking.puja_package.puja.name if booking.puja_package_id and booking.puja_package.puja_id else 'Ritual',
                'time_label': booking.get_time_window_label() if hasattr(booking, 'get_time_window_label') else '',
                'customer_name': (
                    booking.customer.get_full_name() or booking.customer.username
                ) if booking.customer_id else '',
                'status': booking.status,
            }
            for booking in selected_bookings
        ],
        'selected_slots': [
            {
                'value': slot.get('value') or '',
                'label': slot.get('label') or '',
                'available': bool(slot.get('available')),
                'status': slot.get('status') or '',
                'reason': slot.get('reason') or '',
            }
            for slot in selected_slots
        ],
    }
