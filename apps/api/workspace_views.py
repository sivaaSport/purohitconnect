from datetime import time as dt_time

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.workspace import can_act_as_purohit, enable_purohit_workspace
from apps.bookings.location import ensure_home_offer
from apps.bookings.models import Booking, TravelRequest
from apps.bookings.purohit_actions import apply_purohit_booking_status
from apps.bookings.travel import respond_travel_request
from apps.pujas.catalog import puja_sort_key
from apps.pujas.models import Puja
from apps.pujas.package_actions import apply_package_action
from apps.pujas.venues import VENUE_CHOICES
from apps.purohits.availability_actions import apply_availability_action, calendar_state
from apps.purohits.services import ensure_purohit_listing

from .http import api_auth_required, json_error, json_ok, parse_json
from .serializers import booking_payload, package_payload, puja_payload, purohit_payload, travel_request_payload


def _json(request):
    data = parse_json(request)
    if data is None:
        return None, json_error('Invalid JSON body', status=400)
    return data, None


def _listing_or_error(request):
    if not can_act_as_purohit(request.user):
        return None, json_error(
            'Switch to a purohit workspace to manage offerings and incoming bookings.',
            status=403,
        )
    listing = ensure_purohit_listing(request.user)
    if listing is None:
        return None, json_error(
            'Your purohit workspace could not be created yet. Please contact support or ensure cities are seeded.',
            status=400,
        )
    ensure_home_offer(listing)
    return listing, None


def _bucket_bookings(bookings, today):
    need_you, upcoming, past = [], [], []
    for booking in bookings:
        if booking.status == 'pending' or (
            booking.reschedule_status == 'pending' and booking.reschedule_requested_by_customer
        ):
            need_you.append(booking)
        elif booking.status in ('cancelled', 'completed'):
            past.append(booking)
        else:
            upcoming.append(booking)
    return need_you, upcoming, past


@api_auth_required
@require_http_methods(['GET'])
def purohit_dashboard(request):
    listing, err = _listing_or_error(request)
    if err:
        return err
    today = timezone.localdate()
    bookings = list(
        Booking.objects.filter(purohit=listing)
        .select_related('customer', 'puja_package__puja', 'city', 'area')
        .order_by('-updated_at', '-created_at')
    )
    need_you, upcoming, past = _bucket_bookings(bookings, today)
    travel_rows = list(
        listing.travel_requests.select_related('customer', 'city', 'area', 'puja_package__puja')
        .exclude(status='booked')[:30]
    )
    pending_travel = sum(1 for item in travel_rows if item.status == 'pending')
    next_booking = next(
        (
            booking
            for booking in sorted(
                (
                    item
                    for item in bookings
                    if item.status not in ('cancelled', 'completed') and item.event_date and item.event_date >= today
                ),
                key=lambda item: (item.event_date, item.event_time or dt_time.min),
            )
        ),
        None,
    )
    return json_ok({
        'purohit': purohit_payload(listing, request, include_packages=False),
        'stats': {
            'pending_requests': sum(1 for item in bookings if item.status == 'pending'),
            'upcoming_bookings': sum(1 for item in bookings if item.status == 'confirmed'),
            'completed_count': sum(1 for item in bookings if item.status == 'completed'),
            'pending_travel_count': pending_travel,
        },
        'next_booking': booking_payload(next_booking, request) if next_booking else None,
        'need_you': [booking_payload(item, request) for item in need_you[:20]],
        'upcoming': [booking_payload(item, request) for item in upcoming[:20]],
        'travel_requests': [travel_request_payload(item) for item in travel_rows],
        'past_count': len(past),
    })


@api_auth_required
@require_http_methods(['GET'])
def purohit_bookings(request):
    listing, err = _listing_or_error(request)
    if err:
        return err
    today = timezone.localdate()
    bookings = list(
        Booking.objects.filter(purohit=listing)
        .select_related('customer', 'puja_package__puja', 'city', 'area')
        .order_by('-updated_at', '-created_at')
    )
    need_you, upcoming, past = _bucket_bookings(bookings, today)
    bucket = (request.GET.get('bucket') or 'all').strip().lower()
    rows = {'need_you': need_you, 'upcoming': upcoming, 'past': past}.get(bucket, bookings)
    return json_ok({
        'bookings': [booking_payload(item, request) for item in rows[:80]],
        'counts': {
            'need_you': len(need_you),
            'upcoming': len(upcoming),
            'past': len(past),
        },
    })


@api_auth_required
@require_http_methods(['POST'])
def purohit_booking_status(request, booking_id):
    listing, err = _listing_or_error(request)
    if err:
        return err
    data, parse_err = _json(request)
    if parse_err:
        return parse_err
    booking = get_object_or_404(
        Booking.objects.select_related('purohit', 'puja_package__puja', 'customer', 'purohit__profile'),
        booking_id=booking_id,
        purohit=listing,
    )
    ok, code, message = apply_purohit_booking_status(
        booking=booking,
        actor=request.user,
        status=data.get('status'),
        verification_code=data.get('verification_code') or data.get('code') or '',
    )
    booking.refresh_from_db()
    if not ok:
        status = 403 if code == 'forbidden' else 400
        return json_error(message, status=status, code=code)
    return json_ok({
        'code': code,
        'message': message,
        'booking': booking_payload(booking, request),
    })


@api_auth_required
@require_http_methods(['GET'])
def purohit_travel_requests(request):
    listing, err = _listing_or_error(request)
    if err:
        return err
    rows = list(
        listing.travel_requests.select_related('customer', 'city', 'area', 'puja_package__puja')
        .exclude(status='booked')[:40]
    )
    pending = sum(1 for item in rows if item.status == 'pending')
    return json_ok({
        'travel_requests': [travel_request_payload(item) for item in rows],
        'pending_count': pending,
    })


@api_auth_required
@require_http_methods(['POST'])
def purohit_travel_respond(request, request_pk):
    listing, err = _listing_or_error(request)
    if err:
        return err
    data, parse_err = _json(request)
    if parse_err:
        return parse_err
    travel = get_object_or_404(
        TravelRequest.objects.select_related('customer', 'city', 'area', 'puja_package'),
        pk=request_pk,
        purohit=listing,
    )
    ok, code, message = respond_travel_request(
        purohit=listing,
        travel_request=travel,
        decision=data.get('decision'),
        travel_fee=data.get('travel_fee') or 0,
        purohit_response=data.get('purohit_response') or '',
    )
    travel.refresh_from_db()
    if not ok:
        status = 403 if code == 'forbidden' else 400
        if code == 'already_answered':
            return json_ok({
                'code': code,
                'message': message,
                'travel_request': travel_request_payload(travel),
            })
        return json_error(message, status=status, code=code)
    return json_ok({
        'code': code,
        'message': message,
        'travel_request': travel_request_payload(travel),
    })


@api_auth_required
@require_http_methods(['POST'])
def enable_purohit(request):
    listing = enable_purohit_workspace(request.user)
    if listing is None:
        return json_error('Purohit workspace could not be created yet. Ensure cities are seeded.', status=400)
    return json_ok({
        'message': 'Purohit workspace is ready.',
        'purohit': purohit_payload(listing, request),
    })


def _packages_payload(listing, request):
    packages = list(
        listing.puja_packages.select_related('puja', 'puja__category').order_by('puja__name')
    )
    offered_ids = [item.puja_id for item in packages]
    available = list(
        Puja.objects.select_related('category').exclude(id__in=offered_ids)
    )
    available.sort(key=puja_sort_key)
    return {
        'packages': [package_payload(item) for item in packages],
        'available_pujas': [puja_payload(item) for item in available],
        'venue_choices': [{'code': code, 'label': label} for code, label in VENUE_CHOICES],
        'purohit': purohit_payload(listing, request, include_packages=False),
    }


@api_auth_required
@require_http_methods(['GET', 'POST'])
def purohit_packages(request):
    listing, err = _listing_or_error(request)
    if err:
        return err
    if request.method == 'GET':
        return json_ok(_packages_payload(listing, request))
    data, parse_err = _json(request)
    if parse_err:
        return parse_err
    ok, code, message, package = apply_package_action(
        purohit=listing,
        action=data.get('action'),
        data=data,
    )
    payload = _packages_payload(listing, request)
    payload['code'] = code
    payload['message'] = message
    if package is not None:
        payload['package'] = package_payload(package)
    if not ok:
        status = 400
        if code == 'exists':
            status = 409
        return json_error(message, status=status, code=code, **{
            'packages': payload['packages'],
            'available_pujas': payload['available_pujas'],
        })
    return json_ok(payload)


@api_auth_required
@require_http_methods(['GET', 'POST'])
def purohit_calendar(request):
    listing, err = _listing_or_error(request)
    if err:
        return err
    if request.method == 'GET':
        state = calendar_state(
            listing,
            year=request.GET.get('year'),
            month=request.GET.get('month'),
            day=request.GET.get('day'),
            preview_package_id=request.GET.get('preview_package'),
        )
        state['packages'] = [
            package_payload(item)
            for item in listing.puja_packages.select_related('puja', 'puja__category').order_by('puja__name')
        ]
        return json_ok(state)

    data, parse_err = _json(request)
    if parse_err:
        return parse_err
    ok, code, message, extra = apply_availability_action(
        purohit=listing,
        action=data.get('action') or 'block_day',
        data=data,
    )
    listing.refresh_from_db()
    day = (extra or {}).get('redirect_day') or data.get('date') or data.get('day')
    year = data.get('year')
    month = data.get('month')
    if day and (not year or not month):
        year, month = str(day)[:4], str(day)[5:7]
    state = calendar_state(
        listing,
        year=year,
        month=month,
        day=day,
        preview_package_id=data.get('preview_package'),
    )
    state['packages'] = [
        package_payload(item)
        for item in listing.puja_packages.select_related('puja', 'puja__category').order_by('puja__name')
    ]
    state['code'] = code
    state['message'] = message
    if not ok:
        return json_error(message, status=400, code=code, calendar=state)
    return json_ok(state)
