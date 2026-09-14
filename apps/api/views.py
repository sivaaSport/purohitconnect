import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.models import CustomUser, CustomerProfile, OTP, WalletTransaction
from apps.accounts.payment_service import PaymentProcessor, process_wallet_topup
from apps.accounts.utils import send_otp_sms, wallet_service
from apps.accounts.views import validate_phone_number
from apps.accounts.workspace import ensure_devotee_profile
from apps.bookings.location import validate_booking_location
from apps.bookings.models import Booking, TravelRequest
from apps.bookings.travel import submit_travel_request
from apps.bookings.payment_utils import (
    get_booking_payment_options,
    process_booking_payment_mixed,
    process_booking_payment_razorpay,
    process_booking_payment_wallet,
)
from apps.bookings.utils import accept_reschedule, reject_reschedule, request_reschedule
from apps.core.models import Area, City, Language, Notification, ServiceRequest
from apps.core.utils import create_chat_message, mark_booking_chat_as_read, notify_message_recipient
from apps.pujas.catalog import FEATURED_PUJA_NAMES, category_sort_key, puja_sort_key
from apps.pujas.models import Puja, PujaCategory, PurohitPujaPackage
from apps.purohits.models import Purohit
from apps.purohits.utils import get_day_slots, blocks_for_day, _parse_time, check_purohit_availability
from apps.reviews.models import Review
from django.core.exceptions import ValidationError

from .http import api_auth_required, api_public, json_error, json_ok, parse_json
from .models import MobileAuthToken
from .serializers import (
    booking_payload,
    category_payload,
    chat_message_payload,
    notification_payload,
    puja_payload,
    purohit_payload,
    razorpay_order_payload,
    ticket_payload,
    travel_request_payload,
    user_payload,
    wallet_transaction_payload,
)

logger = logging.getLogger(__name__)


def _json(request):
    data = parse_json(request)
    if data is None:
        return None, json_error('Invalid JSON body', status=400)
    return data, None


def _parse_event_time(value):
    if not value:
        return None
    text = str(value).strip()
    text = text.split('(')[0].strip()
    for fmt in ('%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M%p'):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return _parse_time(text)


def _debug_otp_allowed():
    return bool(getattr(settings, 'DEBUG', False) and getattr(settings, 'TWILIO_ALLOW_MOCK', True))


def _money_options(user, amount):
    options = get_booking_payment_options(user, amount)
    wallet = options.get('wallet', {})
    mixed = options.get('mixed')
    return {
        'wallet': {
            'available': bool(wallet.get('available')),
            'balance': float(wallet.get('balance') or 0),
            'shortfall': float(wallet.get('shortfall') or 0),
        },
        'razorpay': {'available': True},
        'mixed': {
            'available': bool(mixed),
            'wallet_amount': float(mixed.get('wallet_amount')) if mixed else 0,
            'razorpay_amount': float(mixed.get('razorpay_amount')) if mixed else 0,
        } if mixed else {'available': False},
    }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@api_public
@require_http_methods(['POST'])
def send_otp(request):
    data, err = _json(request)
    if err:
        return err
    phone = (data.get('phone') or '').strip()
    action = (data.get('action') or 'auto').strip().lower()
    if action not in ('auto', 'login', 'signup'):
        action = 'auto'
    try:
        phone = validate_phone_number(phone)
    except ValidationError as exc:
        return json_error(str(exc))

    user_exists = CustomUser.objects.filter(phone=phone).exists()
    if action == 'auto':
        action = 'login' if user_exists else 'signup'
    if action == 'login' and not user_exists:
        action = 'signup'
    if action == 'signup' and user_exists:
        action = 'login'

    wait = OTP.seconds_until_resend(phone, action)
    if wait > 0:
        return json_error(
            f'Wait {wait} seconds before requesting another OTP.',
            status=429,
            retry_after=wait,
        )
    otp_obj = OTP.generate_otp(phone, action)
    success, message, sid = send_otp_sms(phone, otp_obj.otp_code, action)
    if not success:
        return json_error(message or 'Failed to send OTP')

    payload = {
        'message': f'OTP sent to {phone}',
        'phone': phone,
        'action': action,
        'is_new_user': action == 'signup',
    }
    if _debug_otp_allowed() and str(sid or '').startswith('mock_'):
        payload['debug_otp'] = otp_obj.otp_code
        payload['message'] = f'OTP generated for {phone} (dev mock). Use the on-screen code.'
    return json_ok(payload)


@api_public
@require_http_methods(['POST'])
def verify_otp(request):
    data, err = _json(request)
    if err:
        return err
    phone = (data.get('phone') or '').strip()
    otp_code = (data.get('otp_code') or data.get('otp') or '').strip()
    action = (data.get('action') or 'auto').strip().lower()
    name = (data.get('name') or '').strip()
    if action not in ('auto', 'login', 'signup'):
        action = 'auto'
    try:
        phone = validate_phone_number(phone)
    except ValidationError as exc:
        return json_error(str(exc))
    if not otp_code:
        return json_error('OTP is required')

    user_exists = CustomUser.objects.filter(phone=phone).exists()
    if action == 'auto':
        action = 'login' if user_exists else 'signup'

    success, message = OTP.verify_otp(phone, otp_code, action)
    if not success and action == 'auto':
        other = 'signup' if action == 'login' else 'login'
        success, message = OTP.verify_otp(phone, otp_code, other)
        if success:
            action = other
    if not success:
        return json_error(message, status=401)

    try:
        user = CustomUser.objects.get(phone=phone)
    except CustomUser.DoesNotExist:
        if action != 'signup':
            return json_error('Account not found. Please sign up.', status=404)
        username = (data.get('username') or '').strip() or f"user_{phone.replace('+', '')}"
        first_name, last_name = '', ''
        if name:
            parts = name.split(None, 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''
        role = (data.get('role') or 'customer').strip().lower()
        if role not in ('customer', 'purohit'):
            role = 'customer'
        user = CustomUser.objects.create_user(
            username=username[:150],
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_phone_verified=True,
        )
        if role == 'purohit':
            from apps.accounts.workspace import enable_purohit_workspace
            enable_purohit_workspace(user)
        else:
            CustomerProfile.objects.get_or_create(user=user)
    else:
        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.save(update_fields=['is_phone_verified'])
        if name and not user.first_name:
            parts = name.split(None, 1)
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = parts[1]
            user.save(update_fields=['first_name', 'last_name'])
        ensure_devotee_profile(user)

    token = MobileAuthToken.issue(user, user_agent=request.META.get('HTTP_USER_AGENT', ''))
    return json_ok({
        'message': f'Welcome, {user.get_full_name() or user.username}',
        'token': token.key,
        'user': user_payload(user, request),
    })


@api_auth_required
@require_http_methods(['GET', 'PATCH'])
def me(request):
    if request.method == 'PATCH':
        data, err = _json(request)
        if err:
            return err
        user = request.user
        name = (data.get('name') or '').strip()
        if name:
            parts = name.split(None, 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
        if 'email' in data:
            user.email = (data.get('email') or '').strip()
        city_id = data.get('city_id')
        if city_id:
            city = City.objects.filter(id=city_id).first()
            if city:
                user.city = city
        user.save()
    return json_ok({'user': user_payload(request.user, request)})


@api_auth_required
@require_http_methods(['POST'])
def logout(request):
    token = getattr(request, 'mobile_token', None)
    if token:
        token.delete()
    return json_ok({'message': 'Signed out'})


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

@api_public
@require_http_methods(['GET'])
def categories(request):
    rows = list(PujaCategory.objects.annotate(pujas_count=Count('pujas')))
    rows.sort(key=category_sort_key)
    return json_ok({'categories': [category_payload(c) for c in rows]})


@api_public
@require_http_methods(['GET'])
def pujas(request):
    qs = Puja.objects.select_related('category')
    slug = (request.GET.get('category') or '').strip()
    if slug:
        qs = qs.filter(Q(category__slug=slug) | Q(category__name__iexact=slug))
    category_id = request.GET.get('category_id')
    if category_id:
        qs = qs.filter(category_id=category_id)
    featured = (request.GET.get('featured') or '').strip().lower() in {'1', 'true', 'yes'}
    if featured:
        featured_map = {
            puja.name: puja
            for puja in qs.filter(name__in=FEATURED_PUJA_NAMES)
        }
        rows = [featured_map[name] for name in FEATURED_PUJA_NAMES if name in featured_map]
        if len(rows) < 4:
            extra = list(
                qs.exclude(id__in=[puja.id for puja in rows]).order_by('name')[: 4 - len(rows)]
            )
            rows.extend(extra)
        return json_ok({'pujas': [puja_payload(p) for p in rows]})
    rows = list(qs)
    rows.sort(key=puja_sort_key)
    return json_ok({'pujas': [puja_payload(p) for p in rows]})


@api_public
@require_http_methods(['GET'])
def cities(request):
    items = []
    for city in City.objects.prefetch_related('areas').order_by('name'):
        items.append({
            'id': city.id,
            'name': city.name,
            'state': city.state,
            'areas': [
                {'id': a.id, 'name': a.name, 'pincode': a.pincode}
                for a in city.areas.all().order_by('name')
            ],
        })
    return json_ok({'cities': items})


@api_public
@require_http_methods(['GET'])
def languages(request):
    items = [
        {'id': lang.id, 'name': lang.name, 'native_name': lang.native_name or ''}
        for lang in Language.objects.order_by('name')
    ]
    return json_ok({'languages': items})


_CITY_ALIASES = {
    'bangalore': ('Bangalore', 'Bengaluru'),
    'bengaluru': ('Bangalore', 'Bengaluru'),
    'mumbai': ('Mumbai', 'Bombay'),
    'bombay': ('Mumbai', 'Bombay'),
    'chennai': ('Chennai', 'Madras'),
    'madras': ('Chennai', 'Madras'),
}


def _city_search_names(city):
    names = {city}
    for alias in _CITY_ALIASES.get(city.lower(), ()):
        names.add(alias)
    return names


def _purohit_queryset():
    return Purohit.objects.filter(is_active=True).select_related(
        'city', 'profile', 'profile__user', 'base_area'
    ).prefetch_related('profile__languages_spoken', 'puja_packages__puja')


@api_public
@require_http_methods(['GET'])
def purohit_list(request):
    qs = _purohit_queryset()
    city = (request.GET.get('city') or '').strip()
    if city.isdigit():
        city_id = int(city)
        today = timezone.localdate()
        qs = qs.filter(
            Q(city_id=city_id)
            | Q(service_offers__is_active=True, service_offers__kind='permanent', service_offers__city_id=city_id)
            | Q(
                service_offers__is_active=True,
                service_offers__kind='visit',
                service_offers__city_id=city_id,
                service_offers__end_date__gte=today,
            )
        ).distinct()
    elif city:
        today = timezone.localdate()
        names = _city_search_names(city)
        city_q = Q()
        offer_q = Q()
        visit_q = Q()
        for name in names:
            city_q |= Q(city__name__iexact=name)
            offer_q |= Q(service_offers__city__name__iexact=name)
            visit_q |= Q(service_offers__city__name__iexact=name)
        qs = qs.filter(
            city_q
            | (Q(service_offers__is_active=True, service_offers__kind='permanent') & offer_q)
            | (
                Q(
                    service_offers__is_active=True,
                    service_offers__kind='visit',
                    service_offers__end_date__gte=today,
                )
                & visit_q
            )
        ).distinct()

    if request.GET.get('featured') in ('1', 'true', 'True'):
        qs = qs.filter(is_featured=True)
    puja_id = request.GET.get('puja')
    if puja_id and str(puja_id).isdigit():
        qs = qs.filter(puja_packages__puja_id=int(puja_id)).distinct()
    language_id = request.GET.get('language')
    if language_id and str(language_id).isdigit():
        qs = qs.filter(profile__languages_spoken__id=int(language_id)).distinct()
    query = (request.GET.get('q') or '').strip()
    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(city__name__icontains=query)
            | Q(puja_packages__puja__name__icontains=query)
            | Q(profile__languages_spoken__name__icontains=query)
        ).distinct()
    return json_ok({'purohits': [purohit_payload(p, request) for p in qs]})


@api_public
@require_http_methods(['GET'])
def purohit_detail(request, purohit_id):
    purohit = get_object_or_404(
        _purohit_queryset().prefetch_related('gallery_media'),
        id=purohit_id,
    )
    return json_ok({'purohit': purohit_payload(purohit, request, include_packages=True)})


@api_public
@require_http_methods(['GET'])
def purohit_slots(request, purohit_id):
    purohit = get_object_or_404(Purohit, id=purohit_id, is_active=True)
    date_str = request.GET.get('date')
    package_id = request.GET.get('package_id')
    duration_hours = 2.0
    if package_id:
        package = PurohitPujaPackage.objects.filter(id=package_id, purohit=purohit).first()
        if package:
            duration_hours = package.get_duration_hours()
    if request.GET.get('duration'):
        try:
            duration_hours = float(request.GET.get('duration'))
        except (TypeError, ValueError):
            pass
    if not date_str:
        return json_error('date is required (YYYY-MM-DD)')
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return json_error('Invalid date')
    blocks = blocks_for_day(purohit, date_obj)
    day_fully_blocked = any(b.is_all_day for b in blocks)
    raw_slots = [] if day_fully_blocked else get_day_slots(purohit, date_obj, duration_hours)
    slots = []
    for slot in raw_slots:
        start = slot.get('value') or (slot['start'].strftime('%H:%M') if hasattr(slot.get('start'), 'strftime') else str(slot.get('start', '')))
        end = slot.get('end')
        end_label = end.strftime('%H:%M') if hasattr(end, 'strftime') else str(end or '')
        slots.append({
            'start': start,
            'end': end_label,
            'value': start,
            'label': slot.get('label') or start,
            'available': bool(slot.get('available')),
            'status': slot.get('status'),
            'reason': slot.get('reason') or '',
        })
    return json_ok({
        'date': date_str,
        'duration_hours': duration_hours,
        'blocked': day_fully_blocked,
        'slots': slots,
    })


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

@api_auth_required
@require_http_methods(['POST'])
def create_booking(request):
    data, err = _json(request)
    if err:
        return err
    customer = request.user
    ensure_devotee_profile(customer)

    package_id = data.get('package_id')
    if not package_id:
        return json_error('package_id is required')
    package = PurohitPujaPackage.objects.select_related('purohit', 'puja', 'purohit__profile').filter(id=package_id).first()
    if not package:
        return json_error('Package not found', status=404)

    listing_user_id = getattr(getattr(package.purohit, 'profile', None), 'user_id', None)
    if listing_user_id and listing_user_id == customer.id:
        return json_error('You cannot book your own offering.')

    date_str = (data.get('event_date') or data.get('date') or '').strip()
    time_raw = data.get('event_time') or data.get('time')
    address = (data.get('address') or '').strip()
    city_id = data.get('city_id') or data.get('city')
    area_id = data.get('area_id') or data.get('area')
    venue_type = (data.get('venue_type') or 'home').strip()
    needs_samagri = bool(data.get('needs_samagri'))
    special_requests = (data.get('special_requests') or '').strip()

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return json_error('Valid event_date (YYYY-MM-DD) is required')
    time_obj = _parse_event_time(time_raw)
    if not time_obj:
        return json_error('Please select a time slot')

    duration_hours = package.get_duration_hours()
    is_available, reason = check_purohit_availability(
        package.purohit,
        date_obj,
        time_obj=time_obj,
        duration_hours=duration_hours,
        buffer_minutes=package.get_buffer_minutes(),
    )
    if not is_available:
        return json_error(reason or 'Purohit is not available at that time')

    city = City.objects.filter(id=city_id).first() if city_id else None
    area = Area.objects.filter(id=area_id).first() if area_id else None
    location_ok, location_error, location = validate_booking_location(
        package, venue_type, city, area, address, on_date=date_obj, devotee=customer
    )
    if not location_ok:
        extra = {}
        if location_error and 'request a visit' in location_error:
            extra['code'] = 'travel_request_required'
        return json_error(location_error, **extra)

    total_amount = Decimal(str(package.price))
    if needs_samagri and package.samagri_price:
        total_amount += Decimal(str(package.samagri_price))
    travel_fee = location.get('travel_fee') or 0
    total_amount += Decimal(str(travel_fee))
    travel_request = location.get('travel_request')

    booking = Booking.objects.create(
        customer=customer,
        purohit=package.purohit,
        puja_package=package,
        event_date=date_obj,
        event_time=time_obj,
        duration_hours=duration_hours,
        address=location['address'],
        city=location['city'],
        area=location['area'],
        venue_type=location['venue_type'],
        travel_fee=travel_fee,
        travel_request=travel_request,
        needs_samagri=needs_samagri,
        special_requests=special_requests,
        total_amount=total_amount,
    )
    if travel_request:
        travel_request.status = 'booked'
        travel_request.save(update_fields=['status', 'updated_at'])

    Notification.objects.create(
        user=package.purohit.profile.user,
        title='New Booking Request!',
        message=f'You have a new request for {package.puja.name} on {date_obj}.',
        link='/dashboard/purohit/',
    )

    paid = False
    pay_message = ''
    if data.get('pay_from_wallet'):
        paid, pay_message = process_booking_payment_wallet(booking, customer)
        booking.refresh_from_db()

    return json_ok({
        'message': pay_message or 'Booking created. Complete payment to confirm.',
        'booking': booking_payload(booking, request),
        'paid': paid,
        'payment_options': _money_options(customer, booking.total_amount),
    })


@api_auth_required
@require_http_methods(['GET'])
def my_bookings(request):
    status = (request.GET.get('status') or 'all').strip().lower()
    qs = Booking.objects.filter(customer=request.user).select_related(
        'purohit', 'puja_package__puja', 'city', 'area', 'customer'
    ).order_by('-event_date', '-created_at')
    if status == 'upcoming':
        qs = qs.filter(status__in=['pending', 'confirmed']).exclude(
            event_date__lt=timezone.localdate(), status='completed'
        )
    elif status == 'completed':
        qs = qs.filter(status='completed')
    elif status == 'cancelled':
        qs = qs.filter(status='cancelled')
    elif status in ('pending', 'confirmed'):
        qs = qs.filter(status=status)
    return json_ok({'bookings': [booking_payload(b, request) for b in qs]})


def _customer_booking(request, booking_id):
    return get_object_or_404(
        Booking.objects.select_related('purohit', 'puja_package__puja', 'city', 'area', 'customer'),
        booking_id=booking_id,
        customer=request.user,
    )


def _visible_booking(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related(
            'purohit', 'puja_package__puja', 'city', 'area', 'customer', 'purohit__profile'
        ),
        booking_id=booking_id,
    )
    if booking.customer_id == request.user.id:
        return booking
    listing_id = getattr(getattr(getattr(request.user, 'purohit_profile', None), 'purohit_listing', None), 'id', None)
    if listing_id and listing_id == booking.purohit_id:
        return booking
    from django.http import Http404
    raise Http404()


@api_auth_required
@require_http_methods(['GET'])
def booking_detail(request, booking_id):
    booking = _visible_booking(request, booking_id)
    return json_ok({
        'booking': booking_payload(booking, request),
        'payment_options': _money_options(request.user, booking.total_amount),
    })


@api_auth_required
@require_http_methods(['POST'])
def booking_pay(request, booking_id):
    booking = _customer_booking(request, booking_id)
    if booking.payment_status == 'success':
        return json_ok({
            'message': 'This booking is already paid.',
            'booking': booking_payload(booking, request),
            'already_paid': True,
        })
    data, err = _json(request)
    if err:
        return err
    method = (data.get('method') or data.get('payment_method') or 'wallet').strip().lower()

    if method == 'wallet':
        success, message = process_booking_payment_wallet(booking, request.user)
        booking.refresh_from_db()
        if not success:
            return json_error(message)
        return json_ok({'message': message, 'booking': booking_payload(booking, request), 'paid': True})

    if method == 'mixed':
        success, message, order = process_booking_payment_mixed(booking, request.user)
        booking.refresh_from_db()
        if not success:
            return json_error(message)
        return json_ok({
            'message': message,
            'booking': booking_payload(booking, request),
            'paid': False,
            'razorpay': razorpay_order_payload(order),
        })

    if method == 'razorpay':
        order = PaymentProcessor.create_order(
            booking.total_amount,
            f'booking-{booking.booking_id}',
            description=f'Booking payment {booking.booking_id}',
        )
        if not order:
            return json_error('Could not create payment order. Configure Razorpay or enable mock mode.')
        booking.razorpay_order_id = order['id']
        booking.save(update_fields=['razorpay_order_id'])
        remaining = Decimal(str(booking.total_amount)) - Decimal(str(booking.advance_paid or 0))
        return json_ok({
            'message': 'Complete payment to confirm your ceremony.',
            'booking': booking_payload(booking, request),
            'razorpay': razorpay_order_payload(order),
            'amount': float(remaining if remaining > 0 else booking.total_amount),
        })

    return json_error('Invalid payment method. Use wallet, razorpay, or mixed.')


@api_auth_required
@require_http_methods(['POST'])
def verify_booking_payment(request, booking_id):
    booking = _customer_booking(request, booking_id)
    data, err = _json(request)
    if err:
        return err
    order_id = data.get('razorpay_order_id')
    payment_id = data.get('razorpay_payment_id')
    signature = data.get('razorpay_signature')
    if not all([order_id, payment_id, signature]):
        return json_error('Missing payment details')
    success, message = process_booking_payment_razorpay(booking, order_id, payment_id, signature)
    booking.refresh_from_db()
    if not success:
        return json_error(message)
    return json_ok({'message': message, 'booking': booking_payload(booking, request), 'paid': True})


@api_auth_required
@require_http_methods(['POST'])
def cancel_booking(request, booking_id):
    booking = _customer_booking(request, booking_id)
    if booking.status in ('cancelled', 'completed'):
        return json_error('This booking cannot be cancelled.')
    data, err = _json(request)
    if err:
        return err
    reason = (data.get('reason') or 'Cancelled from mobile app').strip()
    old_status = booking.status
    booking.status = 'cancelled'
    booking.cancellation_reason = reason
    booking.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
    from apps.bookings.utils import record_booking_history
    record_booking_history(
        booking=booking,
        event='cancellation',
        user=request.user,
        message=f'Booking cancelled by {request.user.username}. Reason: {reason}',
        old_value=old_status,
        new_value='cancelled',
    )
    Notification.objects.create(
        user=booking.purohit.profile.user,
        title='Booking Cancelled',
        message=f'Booking {booking.booking_id} has been cancelled. Reason: {reason}',
        link='/dashboard/purohit/',
    )
    if booking.payment_status == 'success':
        Notification.objects.create(
            user=booking.customer,
            title='Refund Initiated',
            message=f'A refund of ₹{booking.total_amount} has been initiated for {booking.booking_id}.',
            link='/dashboard/customer/',
        )
    return json_ok({'message': 'Booking cancelled', 'booking': booking_payload(booking, request)})


@api_auth_required
@require_http_methods(['POST'])
def booking_reschedule(request, booking_id):
    booking = _customer_booking(request, booking_id)
    data, err = _json(request)
    if err:
        return err
    date_str = (data.get('date') or data.get('suggested_date') or '').strip()
    time_raw = data.get('time') or data.get('suggested_time')
    reason = (data.get('reason') or '').strip()
    try:
        suggested_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return json_error('Please choose a new date')
    suggested_time = _parse_event_time(time_raw)
    success, message = request_reschedule(booking, suggested_date, suggested_time, request.user, reason)
    booking.refresh_from_db()
    if not success:
        return json_error(message)
    recipient = booking.purohit.profile.user
    Notification.objects.create(
        user=recipient,
        title='Reschedule Requested by Devotee',
        message=f'{request.user.username} requested to reschedule {booking.booking_id} to {suggested_date}.',
        link='/dashboard/purohit/',
    )
    return json_ok({'message': message, 'booking': booking_payload(booking, request)})


@api_auth_required
@require_http_methods(['POST'])
def booking_reschedule_handle(request, booking_id):
    booking = _customer_booking(request, booking_id)
    data, err = _json(request)
    if err:
        return err
    action = (data.get('action') or '').strip().lower()
    reason = (data.get('reason') or '').strip()
    requester = booking.reschedule_requested_by
    if action == 'accept':
        success, message = accept_reschedule(booking, request.user)
    elif action == 'reject':
        success, message = reject_reschedule(booking, request.user, reason=reason)
    else:
        return json_error('action must be accept or reject')
    booking.refresh_from_db()
    if not success:
        return json_error(message)
    if requester:
        Notification.objects.create(
            user=requester,
            title='Reschedule Accepted' if action == 'accept' else 'Reschedule Declined',
            message=f'Your reschedule request for {booking.booking_id} was {action}ed.',
            link='/dashboard/purohit/' if getattr(requester, 'role', '') == 'purohit' else '/dashboard/customer/',
        )
    return json_ok({'message': message, 'booking': booking_payload(booking, request)})


@api_auth_required
@require_http_methods(['GET', 'POST'])
def booking_chat(request, booking_id):
    booking = _visible_booking(request, booking_id)
    if request.method == 'POST':
        data, err = _json(request)
        if err:
            return err
        text = (data.get('message') or '').strip()
        if not text:
            return json_error('Message cannot be empty')
        msg = create_chat_message(booking=booking, sender=request.user, message_text=text)
        notify_message_recipient(booking, request.user, msg)
    mark_booking_chat_as_read(booking, request.user)
    messages = [
        chat_message_payload(m, request.user)
        for m in booking.messages.select_related('sender').all()
    ]
    return json_ok({'messages': messages, 'booking_id': booking.booking_id})


@api_auth_required
@require_http_methods(['POST'])
def booking_review(request, booking_id):
    booking = _customer_booking(request, booking_id)
    if booking.status != 'completed':
        return json_error('You can only review a completed ritual.')
    data, err = _json(request)
    if err:
        return err
    try:
        rating = int(data.get('rating') or 5)
    except (TypeError, ValueError):
        return json_error('Rating must be 1-5')
    rating = max(1, min(5, rating))
    title = (data.get('title') or 'Review').strip()[:200]
    comment = (data.get('comment') or '').strip()
    review = getattr(booking, 'review', None)
    if review:
        review.rating = rating
        review.title = title
        review.comment = comment
        review.save()
        message = 'Review updated'
    else:
        Review.objects.create(
            reviewer=request.user,
            purohit=booking.purohit,
            booking=booking,
            rating=rating,
            title=title,
            comment=comment,
        )
        message = 'Thank you for your review'
    booking.refresh_from_db()
    return json_ok({'message': message, 'booking': booking_payload(booking, request)})


# ---------------------------------------------------------------------------
# Wallet
# ---------------------------------------------------------------------------

@api_auth_required
@require_http_methods(['GET'])
def wallet(request):
    stats = wallet_service.calculate_wallet_stats(request.user)
    txns = wallet_service.get_transaction_history(request.user, limit=40)
    return json_ok({
        'wallet': {
            'balance': float(stats['current_balance']),
            'total_credited': float(stats['total_credited']),
            'total_debited': float(stats['total_debited']),
            'transactions': [wallet_transaction_payload(t) for t in txns],
        }
    })


@api_auth_required
@require_http_methods(['POST'])
def wallet_topup(request):
    data, err = _json(request)
    if err:
        return err
    try:
        amount = Decimal(str(data.get('amount') or '0'))
        if amount <= 0:
            raise InvalidOperation
    except (InvalidOperation, TypeError, ValueError):
        return json_error('Enter a valid amount')
    order = PaymentProcessor.create_order(
        amount,
        f'wallet-topup-{request.user.id}-{timezone.now().timestamp()}',
        description=f'Wallet top-up for {request.user.get_full_name() or request.user.username}',
    )
    if not order:
        return json_error('Could not start top-up. Configure Razorpay or enable mock mode.')
    wallet_service.create_pending_credit(
        request.user,
        amount,
        'top_up',
        reference=order.get('receipt', ''),
        razorpay_order_id=order['id'],
    )
    return json_ok({
        'message': 'Complete payment to add money',
        'amount': float(amount),
        'razorpay': razorpay_order_payload(order),
    })


@api_auth_required
@require_http_methods(['POST'])
def verify_wallet_payment(request):
    data, err = _json(request)
    if err:
        return err
    order_id = data.get('razorpay_order_id')
    payment_id = data.get('razorpay_payment_id')
    signature = data.get('razorpay_signature')
    try:
        amount = Decimal(str(data.get('amount') or '0'))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal('0')
    if not all([order_id, payment_id, signature]) or amount <= 0:
        pending = WalletTransaction.objects.filter(
            user=request.user, razorpay_order_id=order_id, status='pending'
        ).first()
        if pending:
            amount = pending.amount
    if not all([order_id, payment_id, signature]) or amount <= 0:
        return json_error('Missing payment details')
    success, message, _txn = process_wallet_topup(
        request.user, amount, order_id, payment_id, signature
    )
    if not success:
        return json_error(message)
    request.user.refresh_from_db()
    return json_ok({
        'message': message,
        'wallet_balance': float(request.user.wallet_balance),
        'user': user_payload(request.user, request),
    })


# ---------------------------------------------------------------------------
# Notifications / support
# ---------------------------------------------------------------------------

@api_auth_required
@require_http_methods(['GET'])
def notifications(request):
    qs = Notification.objects.filter(user=request.user, channel='in_app').order_by('-created_at')[:80]
    unread = Notification.objects.filter(user=request.user, channel='in_app', is_read=False).count()
    return json_ok({
        'notifications': [notification_payload(n) for n in qs],
        'unread_count': unread,
    })


@api_auth_required
@require_http_methods(['POST'])
def mark_notification_read(request, notification_id):
    item = get_object_or_404(Notification, id=notification_id, user=request.user)
    item.is_read = True
    item.read_at = timezone.now()
    item.save(update_fields=['is_read', 'read_at', 'updated_at'])
    return json_ok({'notification': notification_payload(item)})


@api_auth_required
@require_http_methods(['POST'])
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    return json_ok({'message': 'All notifications marked read'})


@api_auth_required
@require_http_methods(['GET', 'POST'])
def my_travel_requests(request):
    if request.method == 'POST':
        data, err = _json(request)
        if err:
            return err
        ensure_devotee_profile(request.user)
        package_id = data.get('package_id')
        if not package_id:
            return json_error('package_id is required')
        package = PurohitPujaPackage.objects.select_related(
            'purohit', 'puja', 'purohit__profile'
        ).filter(id=package_id).first()
        if not package:
            return json_error('Package not found', status=404)

        date_str = (data.get('event_date') or data.get('date') or '').strip()
        try:
            preferred_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return json_error('Please choose a date for the visit request.')

        city_id = data.get('city_id') or data.get('city')
        area_id = data.get('area_id') or data.get('area')
        city = City.objects.filter(id=city_id).first() if city_id else None
        area = Area.objects.filter(id=area_id).first() if area_id else None
        _ok, code, message, travel = submit_travel_request(
            customer=request.user,
            package=package,
            city=city,
            area=area,
            address=(data.get('address') or '').strip(),
            venue_type=data.get('venue_type') or 'home',
            preferred_date=preferred_date,
            preferred_time=_parse_event_time(data.get('event_time') or data.get('time')),
            message=(data.get('message') or data.get('special_requests') or '').strip(),
        )
        payload = {'code': code, 'message': message}
        if travel:
            payload['travel_request'] = travel_request_payload(travel)
        if code in ('created', 'already_open'):
            return json_ok(payload)
        status = 403 if code == 'own_listing' else 400
        return json_error(message, status=status, code=code)

    rows = list(
        TravelRequest.objects.filter(customer=request.user)
        .select_related('purohit', 'city', 'area', 'puja_package__puja', 'customer')
        .exclude(status='booked')[:20]
    )
    pending = sum(1 for item in rows if item.status == 'pending')
    return json_ok({
        'travel_requests': [travel_request_payload(item) for item in rows],
        'pending_count': pending,
    })


@api_auth_required
@require_http_methods(['GET', 'POST'])
def support(request):
    if request.method == 'POST':
        data, err = _json(request)
        if err:
            return err
        subject = (data.get('subject') or '').strip()
        description = (data.get('description') or '').strip()
        category = (data.get('category') or 'general').strip()
        if not subject or not description:
            return json_error('Please provide both a subject and description.')
        priority = 'medium'
        if category in {'payment', 'technical'}:
            priority = 'high'
        ticket = ServiceRequest.objects.create(
            user=request.user,
            subject=subject[:200],
            description=description,
            category=category,
            priority=priority,
            status='open',
        )
        staff_users = CustomUser.objects.filter(is_staff=True, is_active=True)[:10]
        for staff in staff_users:
            Notification.objects.create(
                user=staff,
                title='New Support Ticket',
                message=f'{ticket.ticket_id}: {ticket.subject}',
                link='/dashboard/admin/support/',
            )
        return json_ok({'message': 'Support ticket created', 'ticket': ticket_payload(ticket)})
    tickets = ServiceRequest.objects.filter(user=request.user).order_by('-created_at')[:40]
    return json_ok({'tickets': [ticket_payload(t) for t in tickets]})
