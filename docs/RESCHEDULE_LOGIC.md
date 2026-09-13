# Reschedule Logic Documentation

## Overview
The reschedule system has been completely refactored to provide a robust, auditable workflow for rescheduling bookings with proper state tracking and history recording.

## Data Model

### Booking Model Fields
- `reschedule_status`: Current status of any reschedule request
  - `'none'`: No reschedule request or completed/rejected
  - `'pending'`: Awaiting customer response
  - `'accepted'`: Customer accepted the reschedule
  - `'rejected'`: Customer rejected the reschedule

- `reschedule_requested_at`: Timestamp when purohit requested reschedule
- `reschedule_accepted_at`: Timestamp when customer accepted reschedule
- `reschedule_rejected_at`: Timestamp when customer rejected reschedule
- `reschedule_count`: Number of times this booking was rescheduled
- `reschedule_requested_by`: ForeignKey to CustomUser (the purohit requesting)
- `suggested_date`: The proposed new date
- `suggested_time`: The proposed new time

### BookingHistory Model
Comprehensive audit trail with structured event types:
- `event`: One of EVENT_CHOICES (e.g., 'reschedule_requested', 'reschedule_accepted')
- `user`: Who triggered the event
- `message`: Human-readable description
- `old_value`: Previous value (for change tracking)
- `new_value`: New value (for change tracking)
- `created_at`: When event occurred

## Workflow

### 1. Request Reschedule (Purohit → Customer)
**Function**: `apps.bookings.utils.request_reschedule()`
**View**: `dashboard.views.request_reschedule()`

Flow:
1. Purohit selects a new date and time
2. `request_reschedule()` validates booking status
3. Sets `reschedule_status` = 'pending'
4. Sets `reschedule_requested_at` = now
5. Creates BookingHistory with 'reschedule_requested' event
6. Notifies customer of reschedule request

### 2. Accept Reschedule (Customer → Purohit)
**Function**: `apps.bookings.utils.accept_reschedule()`
**View**: `dashboard.views.handle_reschedule()` with action='accept'

Flow:
1. Customer clicks "Accept Reschedule"
2. `accept_reschedule()` validates:
   - Reschedule status is 'pending'
   - Suggested date is available (checks PurohitAvailability)
   - Booking is not cancelled/completed
3. Updates `event_date` and `event_time`
4. Sets `reschedule_status` = 'accepted'
5. Sets `reschedule_accepted_at` = now
6. Increments `reschedule_count`
7. Clears suggested dates
8. Creates BookingHistory with 'reschedule_accepted' event
9. Notifies purohit of acceptance

### 3. Reject Reschedule (Customer → Purohit)
**Function**: `apps.bookings.utils.reject_reschedule()`
**View**: `dashboard.views.handle_reschedule()` with action='reject'

Flow:
1. Customer clicks "Reject Reschedule"
2. `reject_reschedule()` validates reschedule status is 'pending'
3. Sets `reschedule_status` = 'rejected'
4. Sets `reschedule_rejected_at` = now
5. Clears suggested dates
6. Creates BookingHistory with 'reschedule_rejected' event
7. Notifies purohit of rejection

### 4. Reset Reschedule (Purohit)
**Function**: `apps.bookings.utils.reset_reschedule_request()`

Flow:
1. After rejection, purohit can reset and try again
2. Sets `reschedule_status` = 'none'
3. Clears reschedule request fields
4. Allows new reschedule request
5. Creates BookingHistory entry

## Validation

### In request_reschedule():
- ❌ Cannot reschedule if status is 'cancelled'
- ❌ Cannot reschedule if status is 'completed'

### In accept_reschedule():
- ❌ Must have pending reschedule request
- ❌ Purohit must be available on suggested date
- ✅ Checks PurohitAvailability model
- ✅ Checks for conflicting bookings

## Audit Trail

All reschedule events are recorded in BookingHistory:
- Request timestamp
- Acceptance/rejection with timestamp
- Who made the decision
- Original and new dates
- Reason for rejection (if applicable)

To view history:
```python
booking = Booking.objects.get(booking_id='PC-HYD-ABC123')
booking.history.filter(event__startswith='reschedule')
```

## Admin Interface

Access via Django admin:
- View all reschedule events for a booking
- See timeline of request → accept/reject → completion
- Track reschedule count per booking

## Backfill Existing Data

To create history entries for existing bookings without history:
```bash
python manage.py backfill_booking_history
```

This command:
- Creates initial booking creation records
- Records payment successes
- Records acceptance events
- Records ritual start/completion
- Records cancellations

## Future Enhancements

1. ~~Limit reschedule attempts~~: Max 2 reschedules per booking (`RESCHEDULE_MAX_COUNT`)
2. ~~Reschedule deadline~~: Must request 48 hours before event (`RESCHEDULE_MIN_NOTICE_HOURS`)
3. ~~Auto-expire pending~~: Auto-reject if no response in 24h (`RESCHEDULE_PENDING_EXPIRE_HOURS`, command `expire_pending_reschedules`)
4. ~~Customer-initiated reschedule~~: Customer and purohit can both request; counterparty accepts/rejects
5. ~~Reason tracking~~: `reschedule_reason` stored on Booking + history messages

Run auto-expire periodically (preferred: hourly via `run_scheduled_jobs`):
```bash
python manage.py run_scheduled_jobs
# or
python manage.py expire_pending_reschedules
```

Helper scripts:
- Linux/macOS: `scripts/expire_pending_reschedules.sh` (cron)
- Windows: `scripts/expire_pending_reschedules.ps1` (Task Scheduler)

See `docs/PRODUCTION_DEPLOYMENT.md` §12 for setup.
