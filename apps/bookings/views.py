from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from apps.purohits.models import Purohit
from apps.pujas.models import PurohitPujaPackage
from .models import Booking
from apps.core.models import City, Area

@login_required(login_url='accounts:login')
def book_package(request, package_id):
    """View to handle booking a specific package."""
    package = get_object_or_404(PurohitPujaPackage.objects.select_related('purohit', 'puja'), id=package_id)
    
    if request.method == 'POST':
        # Use authenticated user (OTP-based auth implemented)
        customer = request.user
        
        from apps.accounts.workspace import ensure_devotee_profile, set_active_workspace
        ensure_devotee_profile(customer)
        set_active_workspace(request, 'devotee')
        listing_user_id = getattr(getattr(package.purohit, 'profile', None), 'user_id', None)
        if listing_user_id and listing_user_id == customer.id:
            messages.error(request, "You cannot book your own offering. Switch to your purohit workspace to manage it.")
            return redirect('dashboard:purohit')
            
        date = request.POST.get('date')
        time = request.POST.get('time')
        address = request.POST.get('address')
        city_id = request.POST.get('city')
        area_id = request.POST.get('area')
        venue_type = request.POST.get('venue_type')
        needs_samagri = request.POST.get('needs_samagri') == 'on'
        special_requests = request.POST.get('special_requests', '')
        
        # Availability Check
        from apps.purohits.utils import check_purohit_availability, _parse_time
        from datetime import datetime
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            time_obj = _parse_time(time)
            duration_hours = package.get_duration_hours()
            is_available, reason = check_purohit_availability(
                package.purohit,
                date_obj,
                time_obj=time_obj,
                duration_hours=duration_hours,
                buffer_minutes=package.get_buffer_minutes(),
            )
            
            if not is_available:
                messages.error(request, f"Cannot book for {date}: {reason}")
                return redirect('purohits:detail', slug=package.purohit.slug)
            if not time_obj:
                messages.error(request, "Please select a time slot.")
                return redirect('bookings:book', package_id=package.id)
        except (ValueError, TypeError):
            messages.error(request, "Invalid date format.")
            return redirect('purohits:detail', slug=package.purohit.slug)

        from apps.bookings.location import validate_booking_location
        city = City.objects.filter(id=city_id).first() if city_id else None
        area = Area.objects.filter(id=area_id).first() if area_id else None
        location_ok, location_error, location = validate_booking_location(
            package, venue_type, city, area, address, on_date=date_obj, devotee=customer
        )
        if not location_ok:
            messages.error(request, location_error)
            return redirect('bookings:book', package_id=package.id)
        
        total_amount = package.price
        if needs_samagri and package.samagri_price:
            total_amount += package.samagri_price
        travel_fee = location.get('travel_fee') or 0
        total_amount += travel_fee
        travel_request = location.get('travel_request')
            
        booking = Booking.objects.create(
            customer=customer,
            purohit=package.purohit,
            puja_package=package,
            event_date=date,
            event_time=time if time else None,
            duration_hours=duration_hours,
            address=location['address'],
            city=location['city'],
            area=location['area'],
            venue_type=location['venue_type'],
            travel_fee=travel_fee,
            travel_request=travel_request,
            needs_samagri=needs_samagri,
            special_requests=special_requests,
            total_amount=total_amount
        )
        if travel_request:
            travel_request.status = 'booked'
            travel_request.save(update_fields=['status', 'updated_at'])
        
        # Trigger Notification for Purohit
        from apps.core.models import Notification
        Notification.objects.create(
            user=package.purohit.profile.user,
            title="New Booking Request!",
            message=f"You have a new request for {package.puja.name} on {date}.",
            link=f"/dashboard/purohit/"
        )
        
        return redirect('bookings:booking_payment', booking_id=booking.booking_id)

    from calendar import month_name
    from datetime import datetime
    from django.utils import timezone
    from apps.purohits.utils import build_month_calendar, day_status

    today = timezone.localdate()
    duration_hours = package.get_duration_hours()
    buffer_minutes = package.get_buffer_minutes()

    from apps.bookings.models import TravelRequest

    accepted_request = None
    request_id = (request.GET.get('request') or '').strip()
    if request_id:
        accepted_request = TravelRequest.objects.filter(
            request_id=request_id,
            customer=request.user,
            purohit=package.purohit,
            status='accepted',
        ).select_related('city', 'area').first()
        if not (accepted_request and accepted_request.is_open()):
            accepted_request = None

    preselected_date = None
    date_str = (request.GET.get('date') or '').strip()
    if date_str:
        try:
            parsed = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            parsed = None
        if parsed and parsed >= today and day_status(package.purohit, parsed, duration_hours) != 'full':
            preselected_date = parsed
    if not preselected_date and accepted_request:
        preselected_date = accepted_request.preferred_date

    try:
        default_year = preselected_date.year if preselected_date and 'cal_year' not in request.GET else today.year
        default_month = preselected_date.month if preselected_date and 'cal_month' not in request.GET else today.month
        cal_year = int(request.GET.get('cal_year', default_year))
        cal_month = int(request.GET.get('cal_month', default_month))
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

    booking_calendar_weeks = build_month_calendar(
        package.purohit, cal_year, cal_month, duration_hours=duration_hours, today=today
    )

    from apps.bookings.location import location_form_context

    context = {
        'package': package,
        **location_form_context(package, on_date=preselected_date, devotee=request.user),
        'accepted_request': accepted_request,
        'booking_calendar_weeks': booking_calendar_weeks,
        'cal_year': cal_year,
        'cal_month': cal_month,
        'cal_month_label': f'{month_name[cal_month]} {cal_year}',
        'cal_prev_year': prev_year,
        'cal_prev_month': prev_month,
        'cal_next_year': next_year,
        'cal_next_month': next_month,
        'duration_hours': duration_hours,
        'buffer_minutes': buffer_minutes,
        'today': today,
        'preselected_date': preselected_date,
    }
    return render(request, 'bookings/book.html', context)


@login_required(login_url='accounts:login')
@require_POST
def request_travel(request, package_id):
    """Devotee asks a purohit to visit a place they do not already offer."""
    from datetime import datetime
    from apps.bookings.location import covers, resolve_venue
    from apps.bookings.models import TravelRequest
    from apps.core.models import Notification
    from apps.purohits.utils import _parse_time

    package = get_object_or_404(
        PurohitPujaPackage.objects.select_related('purohit', 'puja'), id=package_id
    )
    purohit = package.purohit
    listing_user_id = getattr(getattr(purohit, 'profile', None), 'user_id', None)
    if listing_user_id and listing_user_id == request.user.id:
        messages.error(request, "You cannot request a visit from your own listing.")
        return redirect('dashboard:purohit')
    if not getattr(purohit, 'accepts_travel_requests', True):
        messages.error(request, "This purohit is not accepting travel requests.")
        return redirect('bookings:book', package_id=package.id)

    city = City.objects.filter(id=request.POST.get('city')).first()
    area = Area.objects.filter(id=request.POST.get('area')).first()
    address = (request.POST.get('address') or '').strip()
    venue_type = resolve_venue(package, request.POST.get('venue_type'))
    try:
        preferred_date = datetime.strptime(request.POST.get('date') or '', '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Please choose a date for the visit request.")
        return redirect('bookings:book', package_id=package.id)
    preferred_time = _parse_time(request.POST.get('time'))
    message = (request.POST.get('message') or request.POST.get('special_requests') or '').strip()

    if not city or not area or area.city_id != city.id:
        messages.error(request, "Please choose a city and area.")
        return redirect('bookings:book', package_id=package.id)
    if not address:
        messages.error(request, "Please enter the place details.")
        return redirect('bookings:book', package_id=package.id)
    if venue_type == 'purohit':
        messages.error(request, "A travel request is only needed when the ritual is not at the purohit's place.")
        return redirect('bookings:book', package_id=package.id)
    if covers(purohit, city, area, preferred_date, devotee=request.user):
        messages.info(request, "This purohit already offers that place on that date. You can book directly.")
        return redirect('bookings:book', package_id=package.id)

    existing = TravelRequest.objects.filter(
        customer=request.user,
        purohit=purohit,
        city=city,
        area=area,
        preferred_date=preferred_date,
        status='pending',
    ).first()
    if existing:
        messages.info(request, f"You already have an open request ({existing.request_id}). The purohit will respond there.")
        return redirect('dashboard:customer')

    travel_request = TravelRequest.objects.create(
        customer=request.user,
        purohit=purohit,
        puja_package=package,
        city=city,
        area=area,
        address=address,
        venue_type=venue_type,
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        message=message,
    )
    Notification.objects.create(
        user=purohit.profile.user,
        title='Travel request',
        message=(
            f"{request.user.get_full_name() or request.user.username} asked you to come to "
            f"{area.name}, {city.name} on {preferred_date:%d %b} for {package.puja.name}."
        ),
        link='/dashboard/purohit/#travel-requests',
    )
    messages.success(
        request,
        f"Visit request {travel_request.request_id} sent. You pay only if they accept and you book.",
    )
    return redirect('dashboard:customer')


import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def booking_success(request, booking_id):
    """Confirmation page after successful payment (or redirect unpaid bookings to checkout)."""
    booking = get_object_or_404(
        Booking.objects.select_related(
            'purohit', 'puja_package__puja', 'purohit__profile__user', 'customer'
        ),
        booking_id=booking_id
    )

    # Unpaid bookings go to wallet/Razorpay checkout instead of legacy Razorpay-only page.
    if booking.payment_status != 'success':
        return redirect('bookings:booking_payment', booking_id=booking.booking_id)

    def _whatsapp_phone_number(phone):
        if not phone:
            return None
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if digits.startswith('0'):
            digits = digits.lstrip('0')
        return digits

    purohit_phone = getattr(getattr(booking.purohit, 'profile', None), 'user', None)
    purohit_phone = getattr(purohit_phone, 'phone', None)
    formatted_phone = _whatsapp_phone_number(purohit_phone)
    wa_message = (
        f"Hello! I have booked a {booking.puja_package.puja.name} via PurohitConnect.\n"
        f"Booking ID: {booking.booking_id}\nDate: {booking.event_date}"
    )
    from urllib.parse import quote
    wa_link = None
    if formatted_phone:
        wa_link = f"https://wa.me/{formatted_phone}?text={quote(wa_message)}"

    context = {
        'booking': booking,
        'wa_link': wa_link,
        'payment_confirmed': True,
    }
    return render(request, 'bookings/success.html', context)

@csrf_exempt
def verify_payment(request):
    """Verify Razorpay payment signature and update booking status."""
    if request.method == 'POST':
        data = request.POST
        order_id = data.get('razorpay_order_id')
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            # Verify the signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature': data.get('razorpay_signature')
            })
        except Exception as e:
            return JsonResponse({'status': 'failed', 'error': str(e)})
        
        # Update Booking
        try:
            from django.utils import timezone
            from apps.bookings.utils import record_booking_history
            
            booking = get_object_or_404(Booking, razorpay_order_id=order_id)
            
            # Capture old status
            old_status = booking.payment_status
            
            booking.razorpay_payment_id = data.get('razorpay_payment_id')
            booking.razorpay_signature = data.get('razorpay_signature')
            booking.payment_status = 'success'
            booking.payment_at = timezone.now()
            if booking.status not in ('cancelled', 'completed') and not booking.accepted_at:
                booking.status = 'pending'
            booking.save(update_fields=['payment_status', 'payment_at', 'status', 'razorpay_payment_id', 'razorpay_signature', 'updated_at'])
            
            # Record payment success in history
            record_booking_history(
                booking=booking,
                event='payment_success',
                user=booking.customer,
                message=f"Payment of ₹{booking.total_amount} received successfully (Payment ID: {data.get('razorpay_payment_id')})",
                old_value=old_status,
                new_value='success'
            )
            
            # Notify Purohit
            from apps.core.models import Notification
            Notification.objects.create(
                user=booking.purohit.profile.user,
                title="Payment Received!",
                message=f"Payment of ₹{booking.total_amount} received for booking {booking.booking_id}.",
                link=f"/dashboard/purohit/"
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'failed', 'error': str(e)})
            
    return JsonResponse({'status': 'invalid_request'})


# Wallet-based booking payment views
from .payment_utils import (
    process_booking_payment_wallet, 
    process_booking_payment_razorpay,
    get_booking_payment_options,
    process_booking_payment_mixed
)
from decimal import Decimal

@login_required
def booking_payment(request, booking_id):
    """
    Handle booking payment with options for wallet or Razorpay
    """
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # Verify user is the customer
    if request.user != booking.customer:
        messages.error(request, "You don't have permission to pay for this booking.")
        return redirect('dashboard:customer')
    
    # Check if already paid
    if booking.payment_status == 'success':
        messages.info(request, "This booking has already been paid.")
        return redirect('bookings:success', booking_id=booking_id)
    
    # Get payment options
    payment_options = get_booking_payment_options(request.user, booking.total_amount)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', '').strip()
        
        if payment_method == 'wallet':
            # Process wallet payment
            success, message = process_booking_payment_wallet(booking, request.user)
            
            if success:
                messages.success(request, message)
                return redirect('bookings:success', booking_id=booking_id)
            else:
                messages.error(request, message)
                
        elif payment_method == 'mixed':
            # Process mixed wallet + Razorpay payment
            success, message, razorpay_order = process_booking_payment_mixed(booking, request.user)
            
            if success and razorpay_order:
                # Store booking ID in session for verification
                request.session['booking_payment_id'] = booking.booking_id
                
                context = {
                    'booking': booking,
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                    'razorpay_order_id': razorpay_order['id'],
                    'amount': booking.total_amount - booking.advance_paid,  # Remaining amount
                    'wallet_amount': booking.advance_paid,
                    'is_partial_payment': True,
                    'is_mock_payment': bool(razorpay_order.get('mock')) or str(razorpay_order['id']).startswith('order_mock_'),
                }
                return render(request, 'bookings/payment.html', context)
            else:
                messages.error(request, message)
                
        elif payment_method == 'razorpay':
            # Create Razorpay order for booking (or local mock order)
            from apps.accounts.payment_service import PaymentProcessor, allow_razorpay_mock, is_razorpay_configured

            order = PaymentProcessor.create_order(
                booking.total_amount,
                f"booking-{booking.booking_id}",
                description=f"Booking payment {booking.booking_id}",
            )

            if not order:
                if not is_razorpay_configured():
                    messages.error(
                        request,
                        "Razorpay is not configured. Add real RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET "
                        "in .env, or enable RAZORPAY_ALLOW_MOCK=True for local testing."
                    )
                else:
                    messages.error(request, "Failed to create payment order. Please try again.")
            else:
                booking.razorpay_order_id = order['id']
                booking.save(update_fields=['razorpay_order_id'])

                request.session['booking_payment_id'] = booking.booking_id

                context = {
                    'booking': booking,
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                    'razorpay_order_id': order['id'],
                    'amount': booking.total_amount,
                    'is_mock_payment': bool(order.get('mock')) or str(order['id']).startswith('order_mock_'),
                }
                return render(request, 'bookings/payment.html', context)
        
        else:
            messages.error(request, "Invalid payment method selected.")
    
    context = {
        'booking': booking,
        'payment_options': payment_options,
        'total_amount': booking.total_amount,
    }
    
    return render(request, 'bookings/booking_payment.html', context)


@login_required
@require_POST
def verify_booking_payment(request, booking_id=None):
    """Verify booking payment from Razorpay"""
    
    booking_id = booking_id or request.session.get('booking_payment_id')
    if not booking_id:
        return JsonResponse({'status': 'failed', 'error': 'Missing booking identifier'})
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # Verify user is the customer
    if request.user != booking.customer:
        return JsonResponse({'status': 'failed', 'error': 'Unauthorized'})
    
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return JsonResponse({'status': 'failed', 'error': 'Missing payment details'})
    
    # Process payment
    success, message = process_booking_payment_razorpay(
        booking, razorpay_order_id, razorpay_payment_id, razorpay_signature
    )
    
    if success:
        # Clear session
        request.session.pop('booking_payment_id', None)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'success', 'message': message})
        messages.success(request, message)
        return redirect('bookings:success', booking_id=booking.booking_id)
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'failed', 'error': message})
        messages.error(request, message)
        return redirect('bookings:booking_payment', booking_id=booking.booking_id)
