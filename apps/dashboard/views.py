from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from apps.bookings.models import Booking
from apps.purohits.models import Purohit


def _booking_live_fingerprint(bookings):
    """Stable signature of ritual state. Order and timestamps must not flicker."""
    parts = []
    for item in sorted(bookings, key=lambda booking: booking.booking_id):
        started = '1' if getattr(item, 'started_at', None) else '0'
        done = '1' if getattr(item, 'completed_at', None) else '0'
        try:
            rating = item.review.rating
        except Exception:
            rating = 0
        parts.append(
            f'{item.booking_id}:{item.status}:{item.payment_status}:'
            f'{item.reschedule_status}:{started}:{done}:{rating}'
        )
    return '|'.join(parts)


def _booking_has_review(booking):
    from django.core.exceptions import ObjectDoesNotExist
    try:
        return booking.review is not None
    except ObjectDoesNotExist:
        return False


def _review_prompt_for(bookings):
    pending = [
        item for item in bookings
        if item.status == 'completed' and not _booking_has_review(item)
    ]
    if not pending:
        return None
    pending.sort(key=lambda item: item.completed_at or item.updated_at, reverse=True)
    booking = pending[0]
    puja_name = booking.puja_package.puja.name if booking.puja_package_id else 'your ritual'
    return {
        'booking_id': booking.booking_id,
        'purohit_name': booking.purohit.name,
        'puja_name': puja_name,
    }


def _get_dashboard_template(role: str, ui_variant: str) -> str:
    """Resolve dashboard template by role and optional UI variant."""
    variant = (ui_variant or "luxe").lower()
    template_map = {
        "customer": {
            "classic": "dashboard/customer.html",
            "luxe": "dashboard/customer_v2_luxe.html",
        },
        "purohit": {
            "classic": "dashboard/purohit_dashboard.html",
            "luxe": "dashboard/purohit_dashboard_v2_luxe.html",
        },
    }
    return template_map.get(role, {}).get(variant, template_map[role]["classic"])

def customer_dashboard(request):
    """Dashboard for Devotees (Customers)."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    from apps.accounts.workspace import ensure_devotee_profile, set_active_workspace
    ensure_devotee_profile(request.user)
    set_active_workspace(request, 'devotee')
        
    booking_qs = Booking.objects.filter(customer=request.user).select_related(
        'purohit', 'purohit__profile', 'puja_package', 'puja_package__puja',
        'reschedule_requested_by', 'city', 'area'
    ).prefetch_related('review').order_by('-updated_at', '-created_at')
    service_requests = request.user.service_requests.all().order_by('-created_at')
    
    # Ensure all bookings have verification codes for existing data
    import random
    updated_needed = False
    for b in booking_qs:
        if not b.start_code or not b.complete_code:
            if not b.start_code: b.start_code = str(random.randint(1000, 9999))
            if not b.complete_code: b.complete_code = str(random.randint(1000, 9999))
            b.save()
            updated_needed = True
            
    if updated_needed:
        booking_qs = Booking.objects.filter(customer=request.user).select_related(
            'purohit', 'purohit__profile', 'puja_package', 'puja_package__puja',
            'reschedule_requested_by', 'city', 'area'
        ).prefetch_related('review').order_by('-updated_at', '-created_at')

    bookings = list(booking_qs)
    ongoing_booking = next((item for item in bookings if item.started_at and not item.completed_at), None)

    from calendar import Calendar, month_name
    from django.utils import timezone
    today = timezone.localdate()
    try:
        cal_year = int(request.GET.get('cal_year', today.year))
        cal_month = int(request.GET.get('cal_month', today.month))
    except (TypeError, ValueError):
        cal_year, cal_month = today.year, today.month
    if cal_month < 1 or cal_month > 12:
        cal_year, cal_month = today.year, today.month
    if cal_month == 1:
        prev_year, prev_month = cal_year - 1, 12
    else:
        prev_year, prev_month = cal_year, cal_month - 1
    if cal_month == 12:
        next_year, next_month = cal_year + 1, 1
    else:
        next_year, next_month = cal_year, cal_month + 1

    booking_by_date = {}
    for b in bookings:
        if b.status == 'cancelled' or not b.event_date:
            continue
        booking_by_date.setdefault(b.event_date, []).append(b)

    devotee_calendar_weeks = []
    for week in Calendar(firstweekday=0).monthdatescalendar(cal_year, cal_month):
        row = []
        for day in week:
            day_bookings = booking_by_date.get(day, []) if day.month == cal_month else []
            row.append({
                'date': day,
                'in_month': day.month == cal_month,
                'is_today': day == today,
                'is_past': day < today,
                'bookings': day_bookings,
                'has_booking': bool(day_bookings),
            })
        devotee_calendar_weeks.append(row)
    
    from datetime import time as dt_time
    next_booking = next(
        (
            item for item in sorted(
                (
                    item for item in bookings
                    if item.status not in ('cancelled', 'completed') and item.event_date and item.event_date >= today
                ),
                key=lambda item: (item.event_date, item.event_time or dt_time.min),
            )
        ),
        None,
    )
    upcoming_count = sum(
        1 for item in bookings
        if item.status not in ('cancelled', 'completed') and item.event_date and item.event_date >= today
    )
    awaiting_payment_count = sum(
        1 for item in bookings if item.status != 'cancelled' and item.payment_status == 'pending'
    )
    completed_count = sum(1 for item in bookings if item.status == 'completed')
    days_until_next = None
    if next_booking and next_booking.event_date:
        days_until_next = (next_booking.event_date - today).days
    bookings_need_you = []
    bookings_upcoming = []
    bookings_past = []
    for booking in bookings:
        if booking.status in ('cancelled', 'completed'):
            bookings_past.append(booking)
        elif booking.payment_status != 'success' or (
            booking.reschedule_status == 'pending' and booking.reschedule_requested_by_purohit
        ):
            bookings_need_you.append(booking)
        else:
            bookings_upcoming.append(booking)
    travel_requests = list(
        request.user.travel_requests.select_related(
            'purohit', 'city', 'area', 'puja_package__puja'
        ).exclude(status='booked')[:20]
    )
    pending_travel_count = sum(1 for item in travel_requests if item.status == 'pending')

    from apps.pujas.models import Puja, PujaCategory
    from apps.pujas.catalog import FEATURED_PUJA_NAMES, category_sort_key
    featured = {
        puja.name: puja
        for puja in Puja.objects.filter(name__in=FEATURED_PUJA_NAMES).select_related('category')
    }
    suggested_pujas = [featured[name] for name in FEATURED_PUJA_NAMES if name in featured]
    if len(suggested_pujas) < 4:
        extra = list(
            Puja.objects.select_related('category')
            .exclude(id__in=[p.id for p in suggested_pujas])
            .order_by('name')[: 4 - len(suggested_pujas)]
        )
        suggested_pujas.extend(extra)
    suggested_categories = sorted(PujaCategory.objects.all(), key=category_sort_key)[:4]

    context = {
        'bookings': bookings,
        'total_bookings': len(bookings),
        'service_requests': service_requests,
        'ongoing_booking': ongoing_booking,
        'next_booking': next_booking,
        'upcoming_count': upcoming_count,
        'awaiting_payment_count': awaiting_payment_count,
        'completed_count': completed_count,
        'days_until_next': days_until_next,
        'bookings_need_you': bookings_need_you,
        'bookings_upcoming': bookings_upcoming,
        'bookings_past': bookings_past,
        'suggested_pujas': suggested_pujas,
        'suggested_categories': suggested_categories,
        'travel_requests': travel_requests,
        'pending_travel_count': pending_travel_count,
        'devotee_calendar_weeks': devotee_calendar_weeks,
        'cal_year': cal_year,
        'cal_month': cal_month,
        'cal_month_label': f'{month_name[cal_month]} {cal_year}',
        'cal_prev_year': prev_year,
        'cal_prev_month': prev_month,
        'cal_next_year': next_year,
        'cal_next_month': next_month,
        'ui_variant': request.GET.get('ui', 'luxe').lower(),
        'live_fingerprint': _booking_live_fingerprint(bookings),
        'review_prompt': _review_prompt_for(bookings),
    }
    if getattr(request, 'htmx', False):
        return render(request, 'dashboard/partials/devotee_live.html', context)
    template_name = _get_dashboard_template('customer', context['ui_variant'])
    return render(request, template_name, context)


@login_required(login_url='accounts:login')
def dashboard_live_pulse(request):
    """JSON fingerprint of the devotee's bookings for live dashboard refresh."""
    bookings = Booking.objects.filter(customer=request.user).prefetch_related('review').only(
        'booking_id', 'status', 'payment_status', 'reschedule_status',
        'started_at', 'completed_at', 'updated_at',
    ).order_by('booking_id')
    return JsonResponse({'fingerprint': _booking_live_fingerprint(bookings)})

def admin_support_dashboard(request):
    """Dashboard for Admins to manage Service Requests."""
    if not request.user.is_staff:
        return redirect('core:home')
        
    from apps.core.models import ServiceRequest
    requests = ServiceRequest.objects.all().order_by('-priority', '-created_at')
    
    context = {
        'service_requests': requests,
        'open_count': requests.filter(status='open').count(),
    }
    return render(request, 'dashboard/admin_support.html', context)

def admin_payment_dashboard(request):
    """Dashboard for Admins to view payment analytics and reporting."""
    if not request.user.is_staff:
        return redirect('core:home')
    
    from apps.accounts.models import WalletTransaction, CustomUser
    from apps.bookings.models import Booking
    from django.db.models import Sum, Count, Q
    from django.utils import timezone
    from datetime import timedelta
    
    # Date ranges for analytics
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Wallet Analytics
    total_wallet_balance = CustomUser.objects.aggregate(
        total_balance=Sum('wallet_balance'))['total_balance'] or 0
    
    # Transaction Analytics
    transactions = WalletTransaction.objects.all()
    recent_transactions = transactions.order_by('-created_at')[:20]
    
    # Transaction counts by type
    transaction_stats = transactions.aggregate(
        total_count=Count('id'),
        credit_count=Count('id', filter=Q(transaction_type='credit')),
        debit_count=Count('id', filter=Q(transaction_type='debit')),
        completed_count=Count('id', filter=Q(status='completed')),
        pending_count=Count('id', filter=Q(status='pending')),
        failed_count=Count('id', filter=Q(status='failed')),
    )
    
    # Transaction amounts
    amount_stats = transactions.aggregate(
        total_credited=Sum('amount', filter=Q(transaction_type='credit')) or 0,
        total_debited=Sum('amount', filter=Q(transaction_type='debit')) or 0,
    )
    
    # Recent activity (last 7 days)
    recent_activity = transactions.filter(created_at__date__gte=last_7_days).aggregate(
        recent_credits=Sum('amount', filter=Q(transaction_type='credit')) or 0,
        recent_debits=Sum('amount', filter=Q(transaction_type='debit')) or 0,
        recent_count=Count('id'),
    )
    
    # Top-up vs Booking payments
    reason_stats = transactions.values('reason').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    
    # Booking payment analytics
    bookings = Booking.objects.all()
    booking_payment_stats = bookings.aggregate(
        total_bookings=Count('id'),
        paid_bookings=Count('id', filter=Q(payment_status='paid')),
        pending_payments=Count('id', filter=Q(payment_status='pending')),
        total_revenue=Sum('total_amount', filter=Q(payment_status='paid')) or 0,
    )
    
    # Recent bookings with payments
    recent_paid_bookings = bookings.filter(
        payment_status='paid',
        updated_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-updated_at')[:10]
    
    context = {
        'total_wallet_balance': total_wallet_balance,
        'transaction_stats': transaction_stats,
        'amount_stats': amount_stats,
        'recent_activity': recent_activity,
        'reason_stats': reason_stats,
        'booking_payment_stats': booking_payment_stats,
        'recent_transactions': recent_transactions,
        'recent_paid_bookings': recent_paid_bookings,
        'last_7_days': last_7_days,
        'last_30_days': last_30_days,
    }
    
    return render(request, 'dashboard/admin_payment.html', context)

def update_ticket_status(request, ticket_id):
    """Update status or add notes to a service request."""
    if not request.user.is_staff:
        return redirect('core:home')
        
    from apps.core.models import ServiceRequest
    ticket = get_object_or_404(ServiceRequest, ticket_id=ticket_id)
    
    if request.method == 'POST':
        ticket.status = request.POST.get('status', ticket.status)
        ticket.admin_notes = request.POST.get('admin_notes', ticket.admin_notes)
        ticket.save()
        
        # Notify User (Devotee or Purohit)
        if ticket.user:
            from apps.core.models import Notification
            Notification.objects.create(
                user=ticket.user,
                title=f"Support Ticket Update",
                message=f"Your request {ticket.ticket_id} has been updated to: {ticket.status}",
                link="/dashboard/customer/" if ticket.user.role == 'customer' else "/dashboard/purohit/"
            )
            
        messages.success(request, f"Ticket {ticket_id} updated successfully.")
        
    return redirect('dashboard:admin_support')

# Proper login required with OTP-based authentication
@login_required(login_url='accounts:login')
def purohit_dashboard(request):
    """View for purohit to manage their bookings and profile."""
    # Use authenticated user
    purohit_user = request.user
    
    from apps.accounts.workspace import can_act_as_purohit, set_active_workspace
    if not can_act_as_purohit(purohit_user):
        messages.error(request, "Switch to a purohit workspace to manage offerings and incoming bookings.")
        return redirect('dashboard:customer')
    set_active_workspace(request, 'purohit')

    from apps.bookings.location import ensure_home_offer
    from apps.purohits.services import ensure_purohit_listing
    purohit = ensure_purohit_listing(purohit_user)
    if purohit is None:
        messages.error(
            request,
            "Your purohit workspace could not be created yet. Please contact support or ensure cities are seeded.",
        )
        return redirect('core:about')

    from apps.bookings.location import ensure_home_offer
    ensure_home_offer(purohit)
        
    bookings = list(Booking.objects.filter(purohit=purohit).select_related(
        'customer', 'puja_package', 'puja_package__puja', 'reschedule_requested_by',
        'city', 'area', 'travel_request',
    ).prefetch_related('review').order_by('-updated_at', '-created_at'))
    service_requests = purohit_user.service_requests.all().order_by('-created_at')
    
    # Identify ongoing booking
    ongoing_booking = next((item for item in bookings if item.started_at and not item.completed_at), None)
    
    # Simple stats
    total_bookings = len(bookings)
    upcoming_bookings = sum(1 for item in bookings if item.status == 'confirmed')
    pending_requests = sum(1 for item in bookings if item.status == 'pending')

    from calendar import month_name
    from datetime import date, time as dt_time
    from django.utils import timezone
    from apps.bookings.location import areas_by_city_payload
    from apps.core.models import City
    from apps.pujas.models import Puja
    from apps.pujas.venues import VENUE_CHOICES
    from apps.purohits.utils import build_month_calendar, blocks_for_day, active_bookings_for_day

    packages = list(
        purohit.puja_packages.select_related('puja', 'puja__category').order_by('puja__name')
    )
    offered_ids = [p.puja_id for p in packages]
    available_pujas = list(
        Puja.objects.select_related('category')
        .exclude(id__in=offered_ids)
        .order_by('category__name', 'name')
    )

    preview_package = None
    preview_package_id = (request.GET.get('preview_package') or '').strip()
    if preview_package_id:
        preview_package = next((p for p in packages if str(p.id) == preview_package_id), None)
    if preview_package is None and packages:
        preview_package = max(packages, key=lambda p: p.get_duration_hours())

    calendar_duration = preview_package.get_duration_hours() if preview_package else 2.0

    today = timezone.localdate()
    try:
        cal_year = int(request.GET.get('cal_year', today.year))
        cal_month = int(request.GET.get('cal_month', today.month))
    except (TypeError, ValueError):
        cal_year, cal_month = today.year, today.month
    if cal_month < 1 or cal_month > 12:
        cal_year, cal_month = today.year, today.month

    if cal_month == 12:
        next_year, next_month = cal_year + 1, 1
    else:
        next_year, next_month = cal_year, cal_month + 1
    if cal_month == 1:
        prev_year, prev_month = cal_year - 1, 12
    else:
        prev_year, prev_month = cal_year, cal_month - 1

    calendar_weeks = build_month_calendar(
        purohit, cal_year, cal_month, duration_hours=calendar_duration, today=today
    )

    selected_date_str = request.GET.get('day') or ''
    selected_day = None
    selected_blocks = []
    selected_day_bookings = []
    selected_slots = []
    if selected_date_str:
        try:
            selected_day = date.fromisoformat(selected_date_str)
            selected_blocks = blocks_for_day(purohit, selected_day)
            selected_day_bookings = list(active_bookings_for_day(purohit, selected_day))
            from apps.purohits.utils import get_day_slots
            selected_slots = get_day_slots(purohit, selected_day, duration_hours=calendar_duration)
        except ValueError:
            selected_day = None

    next_booking = next(
        (
            booking for booking in sorted(
                (item for item in bookings if item.status not in ('cancelled', 'completed') and item.event_date and item.event_date >= today),
                key=lambda item: (item.event_date, item.event_time or dt_time.min),
            )
        ),
        None,
    )
    next_pending = next((item for item in bookings if item.status == 'pending'), None)
    days_until_next = None
    if next_booking and next_booking.event_date:
        days_until_next = (next_booking.event_date - today).days
    completed_count = sum(1 for item in bookings if item.status == 'completed')
    bookings_need_you = []
    bookings_upcoming = []
    bookings_past = []
    for booking in bookings:
        if booking.status == 'pending' or (
            booking.reschedule_status == 'pending' and booking.reschedule_requested_by_customer
        ):
            bookings_need_you.append(booking)
        elif booking.status in ('cancelled', 'completed'):
            bookings_past.append(booking)
        else:
            bookings_upcoming.append(booking)
    travel_requests = list(
        purohit.travel_requests.select_related(
            'customer', 'city', 'area', 'puja_package__puja'
        ).filter(status__in=['pending', 'accepted'])
    )
    pending_travel_count = sum(1 for item in travel_requests if item.status == 'pending')
    active_offers = list(purohit.service_offers.filter(is_active=True).select_related('city', 'area'))
    permanent_offers = [offer for offer in active_offers if offer.kind == 'permanent']
    visit_offers = [offer for offer in active_offers if offer.kind == 'visit']
    
    context = {
        'purohit': purohit,
        'bookings': bookings,
        'service_requests': service_requests,
        'total_bookings': total_bookings,
        'upcoming_bookings': upcoming_bookings,
        'pending_requests': pending_requests,
        'ongoing_booking': ongoing_booking,
        'next_booking': next_booking,
        'next_pending': next_pending,
        'days_until_next': days_until_next,
        'completed_count': completed_count,
        'bookings_need_you': bookings_need_you,
        'bookings_upcoming': bookings_upcoming,
        'bookings_past': bookings_past,
        'packages': packages,
        'available_pujas': available_pujas,
        'venue_choices': VENUE_CHOICES,
        'calendar_weeks': calendar_weeks,
        'cal_year': cal_year,
        'cal_month': cal_month,
        'cal_month_label': f'{month_name[cal_month]} {cal_year}',
        'cal_prev_year': prev_year,
        'cal_prev_month': prev_month,
        'cal_next_year': next_year,
        'cal_next_month': next_month,
        'today': today,
        'selected_day': selected_day,
        'selected_blocks': selected_blocks,
        'selected_day_bookings': selected_day_bookings,
        'selected_slots': selected_slots,
        'calendar_duration': calendar_duration,
        'preview_package': preview_package,
        'work_start': purohit.work_start,
        'work_end': purohit.work_end,
        'service_cities': City.objects.all().order_by('name'),
        'service_areas_by_city': areas_by_city_payload(),
        'permanent_offers': permanent_offers,
        'visit_offers': visit_offers,
        'places_count': len(permanent_offers) + len(visit_offers),
        'travel_requests': travel_requests,
        'pending_travel_count': pending_travel_count,
        'ui_variant': request.GET.get('ui', 'luxe').lower(),
    }
    template_name = _get_dashboard_template('purohit', context['ui_variant'])
    return render(request, template_name, context)

def update_booking_status(request, booking_id):
    """View to update booking status from dashboard."""
    if request.method == 'POST':
        booking = get_object_or_404(
            Booking.objects.select_related('purohit', 'puja_package__puja', 'customer'),
            booking_id=booking_id,
        )
        from apps.bookings.purohit_actions import apply_purohit_booking_status
        ok, _code, message = apply_purohit_booking_status(
            booking=booking,
            actor=request.user,
            status=request.POST.get('status'),
            verification_code=request.POST.get('verification_code'),
        )
        if ok:
            messages.success(request, message)
        else:
            messages.error(request, message)
    return redirect('dashboard:purohit')

def request_reschedule(request, booking_id):
    """Purohit or customer requests a reschedule for a booking."""
    if request.method == 'POST':
        booking = get_object_or_404(Booking, booking_id=booking_id)
        suggested_date = request.POST.get('suggested_date')
        suggested_time = request.POST.get('suggested_time')
        reason = (request.POST.get('reason') or '').strip()

        # Authorization: customer of booking or purohit assigned to booking
        is_customer = request.user == booking.customer
        is_purohit = (
            hasattr(request.user, 'purohit_profile')
            and getattr(request.user.purohit_profile, 'purohit_listing', None) == booking.purohit
        )
        if not (is_customer or is_purohit or request.user.is_staff):
            messages.error(request, "You don't have permission to reschedule this booking.")
            return redirect('core:home')

        if suggested_date:
            from apps.bookings.utils import request_reschedule as request_reschedule_util
            success, message = request_reschedule_util(
                booking=booking,
                suggested_date=suggested_date,
                suggested_time=suggested_time,
                requested_by=request.user,
                reason=reason
            )

            if success:
                from apps.core.models import Notification
                if is_customer:
                    recipient = booking.purohit.profile.user
                    title = "Reschedule Requested by Devotee"
                    notify_msg = (
                        f"{request.user.username} requested to reschedule {booking.booking_id} "
                        f"to {suggested_date}."
                    )
                    link = "/dashboard/purohit/"
                else:
                    recipient = booking.customer
                    title = "Reschedule Requested"
                    notify_msg = (
                        f"Purohit {booking.purohit.name} requested to reschedule to {suggested_date}."
                    )
                    link = "/dashboard/customer/"

                Notification.objects.create(
                    user=recipient,
                    title=title,
                    message=notify_msg,
                    link=link
                )
                messages.success(request, message)
            else:
                messages.error(request, message)
        else:
            messages.error(request, "Please select a date for rescheduling.")

    return redirect('dashboard:purohit' if getattr(request.user, 'role', '') == 'purohit' else 'dashboard:customer')


def handle_reschedule(request, booking_id):
    """Counterparty accepts or rejects a reschedule request."""
    if request.method == 'POST':
        booking = get_object_or_404(Booking, booking_id=booking_id)
        action = request.POST.get('action')  # 'accept' or 'reject'
        reason = (request.POST.get('reason') or '').strip()

        from apps.bookings.utils import accept_reschedule, reject_reschedule
        from apps.core.models import Notification

        requester = booking.reschedule_requested_by
        if action == 'accept':
            success, message = accept_reschedule(booking, request.user)
            if success:
                if requester:
                    Notification.objects.create(
                        user=requester,
                        title="Reschedule Accepted",
                        message=f"Your reschedule request for {booking.booking_id} was accepted.",
                        link="/dashboard/purohit/" if getattr(requester, 'role', '') == 'purohit' else "/dashboard/customer/"
                    )
                messages.success(request, message)
            else:
                messages.error(request, message)

        elif action == 'reject':
            success, message = reject_reschedule(booking, request.user, reason=reason)
            if success:
                if requester:
                    Notification.objects.create(
                        user=requester,
                        title="Reschedule Declined",
                        message=f"Your reschedule request for {booking.booking_id} was declined.",
                        link="/dashboard/purohit/" if getattr(requester, 'role', '') == 'purohit' else "/dashboard/customer/"
                    )
                messages.info(request, message)
            else:
                messages.error(request, message)

    return redirect('dashboard:purohit' if getattr(request.user, 'role', '') == 'purohit' else 'dashboard:customer')

def cancel_booking(request, booking_id):
    """Purohit or Customer cancels a booking with simulated refund."""
    if request.method == 'POST':
        booking = get_object_or_404(Booking, booking_id=booking_id)
        reason = request.POST.get('reason', 'No reason provided')
        
        # Record original status for history
        old_status = booking.status
        
        booking.status = 'cancelled'
        booking.cancellation_reason = reason
        booking.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
        
        # Record cancellation in history
        from apps.bookings.utils import record_booking_history
        record_booking_history(
            booking=booking,
            event='cancellation',
            user=request.user,
            message=f"Booking cancelled by {request.user.username}. Reason: {reason}",
            old_value=old_status,
            new_value='cancelled'
        )
        
        # Determine notification recipient
        recipient = booking.customer if request.user.role == 'purohit' else booking.purohit.profile.user
        
        from apps.core.models import Notification
        Notification.objects.create(
            user=recipient,
            title="Booking Cancelled",
            message=f"Booking {booking_id} has been cancelled. Reason: {reason}",
            link="/dashboard/customer/" if recipient.role == 'customer' else "/dashboard/purohit/"
        )
        
        if booking.payment_status == 'success':
            # Simulated Refund Notification
            Notification.objects.create(
                user=booking.customer,
                title="Refund Initiated",
                message=f"A full refund of ₹{booking.total_amount} has been initiated for cancelled booking {booking_id}.",
                link="/dashboard/customer/"
            )
            messages.success(request, "Booking cancelled and refund initiated.")
        else:
            messages.success(request, "Booking cancelled successfully.")
            
    from apps.accounts.workspace import workspace_home_name
    return redirect(workspace_home_name(request))

@login_required(login_url='accounts:login')
def manage_package(request):
    """Add, update, or remove a purohit's offered puja packages."""
    if request.method != 'POST':
        return redirect('dashboard:purohit')

    from apps.accounts.workspace import can_act_as_purohit, set_active_workspace
    if not can_act_as_purohit(request.user):
        messages.error(request, "Only purohits can manage service packages.")
        return redirect('dashboard:customer')
    set_active_workspace(request, 'purohit')

    from apps.pujas.package_actions import apply_package_action
    from apps.purohits.services import ensure_purohit_listing

    purohit = ensure_purohit_listing(request.user)
    if purohit is None:
        messages.error(request, "Purohit workspace is not ready yet.")
        return redirect('dashboard:purohit')

    ok, _code, message, _package = apply_package_action(
        purohit=purohit,
        action=request.POST.get('action'),
        data=request.POST,
    )
    if ok:
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect(reverse('dashboard:purohit') + '#my-pujas')


def _purohit_workspace(request):
    from apps.accounts.workspace import can_act_as_purohit, set_active_workspace
    from apps.purohits.services import ensure_purohit_listing

    if not can_act_as_purohit(request.user):
        return None, redirect('dashboard:customer')
    set_active_workspace(request, 'purohit')
    purohit = ensure_purohit_listing(request.user)
    if purohit is None:
        messages.error(request, "Purohit workspace is not ready yet.")
        return None, redirect('dashboard:purohit')
    return purohit, None


def _optional_id(raw):
    value = (raw or '').strip()
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _area_in_city(city, raw):
    from apps.core.models import Area
    area_id = _optional_id(raw)
    if not city or not area_id:
        return None
    return Area.objects.filter(id=area_id, city=city).first()


@login_required(login_url='accounts:login')
def update_service_locations(request):
    """Let a purohit set home city, base area, and travel-request policy."""
    if request.method != 'POST':
        return redirect(reverse('dashboard:purohit') + '#service-locations')

    from apps.bookings.location import ensure_home_offer
    from apps.core.models import Area, City
    from apps.purohits.models import PurohitServiceOffer

    purohit, error_response = _purohit_workspace(request)
    if error_response:
        if purohit is None:
            messages.error(request, "Service locations are only available for Purohits.")
        return error_response

    city = City.objects.filter(id=_optional_id(request.POST.get('city'))).first()
    if not city:
        messages.error(request, "Please choose a valid city.")
        return redirect(reverse('dashboard:purohit') + '#service-locations')

    base = _area_in_city(city, request.POST.get('base_area'))
    purohit.city = city
    purohit.base_area = base
    purohit.travel_note = (request.POST.get('travel_note') or '').strip()[:240]
    purohit.accepts_travel_requests = request.POST.get('accepts_travel_requests') == 'on'
    purohit.save(update_fields=['city', 'base_area', 'travel_note', 'accepts_travel_requests', 'updated_at'])
    ensure_home_offer(purohit)

    area_ids = request.POST.getlist('service_areas')
    if area_ids:
        areas = list(Area.objects.filter(id__in=area_ids, city=city).order_by('name'))
        if base and base.id not in {area.id for area in areas}:
            areas.append(base)
        for area in areas:
            PurohitServiceOffer.objects.get_or_create(
                purohit=purohit,
                city=city,
                area=area,
                kind=PurohitServiceOffer.KIND_PERMANENT,
                defaults={'is_active': True},
            )
        purohit.service_areas.set(areas)

    messages.success(
        request,
        f"Home location updated. Based in {base.name if base else city.name}.",
    )
    return redirect(reverse('dashboard:purohit') + '#service-locations')


@login_required(login_url='accounts:login')
def update_travel_policy(request):
    """Save only whether the purohit accepts travel requests, plus the note."""
    if request.method != 'POST':
        return redirect(reverse('dashboard:purohit') + '#travel-requests')

    purohit, error_response = _purohit_workspace(request)
    if error_response:
        return error_response

    purohit.travel_note = (request.POST.get('travel_note') or '').strip()[:240]
    choice = (request.POST.get('accepts_travel_requests') or '').strip().lower()
    purohit.accepts_travel_requests = choice in {'on', 'true', '1', 'yes'}
    purohit.save(update_fields=['travel_note', 'accepts_travel_requests', 'updated_at'])
    if purohit.accepts_travel_requests:
        messages.success(request, "Travel requests are on. Devotees can ask you to visit a new place.")
    else:
        messages.success(request, "Travel requests are off. Devotees can only book places you already offer.")
    return redirect(reverse('dashboard:purohit') + '#travel-requests')


@login_required(login_url='accounts:login')
def add_service_offer(request):
    if request.method != 'POST':
        return redirect(reverse('dashboard:purohit') + '#service-locations')

    from datetime import datetime
    from apps.core.models import City
    from apps.purohits.models import PurohitServiceOffer

    purohit, error_response = _purohit_workspace(request)
    if error_response:
        return error_response

    city = City.objects.filter(id=_optional_id(request.POST.get('city'))).first()
    if not city:
        messages.error(request, "Please choose a city for this offer.")
        return redirect(reverse('dashboard:purohit') + '#service-locations')

    area = _area_in_city(city, request.POST.get('area'))
    kind = request.POST.get('kind') or PurohitServiceOffer.KIND_PERMANENT
    if kind not in {PurohitServiceOffer.KIND_PERMANENT, PurohitServiceOffer.KIND_VISIT}:
        kind = PurohitServiceOffer.KIND_PERMANENT
    note = (request.POST.get('note') or '').strip()[:240]
    start_date = end_date = None
    if kind == PurohitServiceOffer.KIND_VISIT:
        try:
            start_date = datetime.strptime(request.POST.get('start_date') or '', '%Y-%m-%d').date()
            end_date = datetime.strptime(request.POST.get('end_date') or '', '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "A visit needs a start and end date.")
            return redirect(reverse('dashboard:purohit') + '#service-locations')
        if end_date < start_date:
            messages.error(request, "Visit end date must be on or after the start date.")
            return redirect(reverse('dashboard:purohit') + '#service-locations')
        PurohitServiceOffer.objects.create(
            purohit=purohit,
            city=city,
            area=area,
            kind=kind,
            start_date=start_date,
            end_date=end_date,
            note=note,
        )
        messages.success(request, f"Visit added: {city.name} {start_date:%d %b}–{end_date:%d %b}.")
    else:
        existing = PurohitServiceOffer.objects.filter(
            purohit=purohit,
            city=city,
            kind=PurohitServiceOffer.KIND_PERMANENT,
        )
        existing = existing.filter(area=area) if area else existing.filter(area__isnull=True)
        offer = existing.first()
        created = offer is None
        if offer is None:
            offer = PurohitServiceOffer.objects.create(
                purohit=purohit,
                city=city,
                area=area,
                kind=PurohitServiceOffer.KIND_PERMANENT,
                note=note,
            )
        else:
            offer.is_active = True
            offer.note = note or offer.note
            offer.save(update_fields=['is_active', 'note'])
            messages.info(request, "That permanent offer is already on your list.")
        if created:
            messages.success(
                request,
                f"Now always taking work in {area.name if area else city.name}.",
            )
        if area:
            purohit.service_areas.add(area)
        if not purohit.base_area_id and area and city.id == purohit.city_id:
            purohit.base_area = area
            purohit.save(update_fields=['base_area', 'updated_at'])
    return redirect(reverse('dashboard:purohit') + '#service-locations')


@login_required(login_url='accounts:login')
def delete_service_offer(request, offer_pk):
    if request.method != 'POST':
        return redirect(reverse('dashboard:purohit') + '#service-locations')

    from apps.purohits.models import PurohitServiceOffer

    purohit, error_response = _purohit_workspace(request)
    if error_response:
        return error_response

    offer = get_object_or_404(PurohitServiceOffer, pk=offer_pk, purohit=purohit)
    label = offer.label()
    if offer.area_id:
        purohit.service_areas.remove(offer.area)
    offer.delete()
    messages.success(request, f"Removed offer: {label}.")
    return redirect(reverse('dashboard:purohit') + '#service-locations')


@login_required(login_url='accounts:login')
def respond_travel_request(request, request_pk):
    if request.method != 'POST':
        return redirect(reverse('dashboard:purohit') + '#travel-requests')

    from apps.bookings.models import TravelRequest
    from apps.bookings.travel import respond_travel_request as decide_travel_request

    purohit, error_response = _purohit_workspace(request)
    if error_response:
        return error_response

    travel_request = get_object_or_404(TravelRequest, pk=request_pk, purohit=purohit)
    ok, code, message = decide_travel_request(
        purohit=purohit,
        travel_request=travel_request,
        decision=request.POST.get('decision'),
        travel_fee=request.POST.get('travel_fee') or 0,
        purohit_response=request.POST.get('purohit_response'),
    )
    if ok:
        messages.success(request, message)
    elif code == 'already_answered':
        messages.info(request, message)
    else:
        messages.error(request, message)
    return redirect(reverse('dashboard:purohit') + '#travel-requests')


@login_required(login_url='accounts:login')
def toggle_availability(request):
    """Manage timed/full-day availability blocks for the logged-in purohit."""
    if request.method != 'POST':
        return redirect(reverse('dashboard:purohit') + '#calendar')

    from apps.purohits.availability_actions import apply_availability_action
    from apps.purohits.services import ensure_purohit_listing

    from apps.accounts.workspace import can_act_as_purohit, set_active_workspace
    if not can_act_as_purohit(request.user):
        messages.error(request, "Availability settings are only available for Purohits.")
        return redirect('dashboard:customer')
    set_active_workspace(request, 'purohit')

    purohit = ensure_purohit_listing(request.user)
    if purohit is None:
        messages.error(request, "Purohit workspace is not ready yet.")
        return redirect('dashboard:purohit')

    date_str = request.POST.get('date')
    preview_package = (request.POST.get('preview_package') or '').strip()
    ok, _code, message, extra = apply_availability_action(
        purohit=purohit,
        action=request.POST.get('action') or 'block_day',
        data=request.POST,
    )
    if ok:
        messages.success(request, message)
    else:
        messages.error(request, message)
    redirect_day = (extra or {}).get('redirect_day') or date_str or ''

    params = []
    if redirect_day:
        params.append(f"cal_year={redirect_day[:4]}")
        params.append(f"cal_month={int(redirect_day[5:7])}")
        params.append(f"day={redirect_day}")
    if preview_package:
        params.append(f"preview_package={preview_package}")
    url = reverse('dashboard:purohit')
    if params:
        url = f"{url}?{'&'.join(params)}#calendar"
    else:
        url = f"{url}#calendar"
    return redirect(url)

def booking_chat(request, booking_id):
    """Internal chat view for a specific booking."""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # AGGRESSIVE CLEAR: Purge all session messages to kill redundant boxes
    storage = messages.get_messages(request)
    for _ in storage:
        pass
    storage.used = True
    
    # Security check: Ensure user is part of this booking
    is_customer = request.user == booking.customer
    is_purohit = hasattr(request.user, 'purohit_profile') and request.user.purohit_profile.purohit_listing == booking.purohit
    
    if not (is_customer or is_purohit):
        return redirect('core:home')

    # MARK AS ACTIVE CHAT (for suppressing notifications)
    from django.core.cache import cache
    cache_key = f"active_chat_user_{request.user.id}"
    cache.set(cache_key, booking_id, 30)  # Active for 30 seconds

    from apps.core.models import ChatMessage
    from apps.core.utils import create_chat_message, notify_message_recipient, mark_booking_chat_as_read
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        
        if message_text:
            try:
                # Create message using utility
                msg = create_chat_message(
                    booking=booking,
                    sender=request.user,
                    message_text=message_text
                )
                
                # Notify recipient if they're not in chat
                notify_message_recipient(booking, request.user, msg)
                
                # If HTMX, return just the message partial for instant appending
                if request.htmx:
                    return render(request, 'dashboard/partials/chat_messages.html', {
                        'chat_messages': [msg],
                        'user': request.user
                    })
                
                messages.success(request, "Message sent!")
            except Exception as e:
                messages.error(request, f"Failed to send message: {str(e)}")
        else:
            messages.warning(request, "Message cannot be empty.")

    # Mark all messages in this chat as read for current user
    mark_booking_chat_as_read(booking, request.user)
    
    chat_messages = booking.messages.all().order_by('created_at')
    
    context = {
        'booking': booking,
        'chat_messages': chat_messages,
        'is_customer': is_customer,
        'is_purohit': is_purohit,
        'messages': None,  # Explicitly block base.html messages loop
    }
    return render(request, 'dashboard/chat.html', context)
