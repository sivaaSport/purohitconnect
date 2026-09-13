from decimal import Decimal

from django.conf import settings


def _media_url(request, filefield):
    if not filefield:
        return ''
    try:
        url = filefield.url
    except ValueError:
        return ''
    if not url:
        return ''
    if url.startswith(('http://', 'https://')):
        return url
    if not url.startswith('/'):
        url = '/' + url
    if request:
        return request.build_absolute_uri(url)
    return url


def _money(value):
    if value is None:
        return 0.0
    return float(Decimal(str(value)))


def user_payload(user, request=None):
    name = (user.get_full_name() or '').strip() or user.username
    city = user.city.name if getattr(user, 'city_id', None) else ''
    return {
        'id': user.id,
        'phone': user.phone or '',
        'username': user.username,
        'name': name,
        'first_name': user.first_name or '',
        'last_name': user.last_name or '',
        'email': user.email or '',
        'role': user.role,
        'wallet_balance': _money(user.wallet_balance),
        'is_phone_verified': bool(user.is_phone_verified),
        'city': city,
        'city_id': user.city_id,
        'avatar_url': _media_url(request, getattr(user, 'avatar', None)),
    }


def category_payload(category):
    return {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'icon': category.icon or 'home',
        'description': category.description or '',
        'pujas_count': getattr(category, 'pujas_count', None)
        if getattr(category, 'pujas_count', None) is not None
        else category.pujas.count(),
    }


def puja_payload(puja):
    return {
        'id': puja.id,
        'name': puja.name,
        'slug': puja.slug,
        'category_id': puja.category_id,
        'category_name': puja.category.name if puja.category_id else '',
        'description': puja.description or '',
        'base_duration_hours': _money(puja.base_duration_hours),
        'typical_venues': puja.get_typical_venues() if hasattr(puja, 'get_typical_venues') else [],
    }


def gallery_item_payload(item, request=None):
    media_type = item.media_type or 'photo'
    title = (item.title or '').strip()
    if not title:
        title = 'Video' if media_type == 'video' else 'Puja photo'
    return {
        'id': item.id,
        'media_type': media_type,
        'url': _media_url(request, item.file),
        'title': title,
        'caption': (item.caption or '').strip(),
        'is_featured': bool(item.is_featured),
    }


def package_payload(package):
    venues = []
    if hasattr(package, 'get_venue_items'):
        venues = [
            {'code': item.get('code', ''), 'label': item.get('label', '')}
            if isinstance(item, dict)
            else {'code': str(item), 'label': str(item)}
            for item in package.get_venue_items()
        ]
    return {
        'id': package.id,
        'puja_id': package.puja_id,
        'puja_name': package.puja.name if package.puja_id else '',
        'puja_description': package.puja.description if package.puja_id else '',
        'price': _money(package.price),
        'includes_samagri': bool(package.includes_samagri),
        'samagri_price': _money(package.samagri_price or 0),
        'custom_description': package.custom_description or '',
        'duration_hours': package.get_duration_hours(),
        'buffer_minutes': package.get_buffer_minutes(),
        'venues': venues,
        'venue_notes': package.venue_notes or '',
    }


def purohit_payload(purohit, request=None, include_packages=False):
    profile = getattr(purohit, 'profile', None)
    languages = []
    if profile is not None:
        languages = list(profile.languages_spoken.values_list('name', flat=True))
    packages = []
    gallery = []
    if include_packages:
        packages = [
            package_payload(pkg)
            for pkg in purohit.puja_packages.select_related('puja', 'puja__category').all()
        ]
        gallery = [
            gallery_item_payload(item, request)
            for item in purohit.gallery_media.all()[:24]
        ]
    avatar = ''
    if profile is not None:
        avatar = _media_url(request, getattr(profile.user, 'avatar', None))
    return {
        'id': purohit.id,
        'name': purohit.name,
        'slug': purohit.slug,
        'city': purohit.city.name if purohit.city_id else 'India',
        'city_id': purohit.city_id,
        'base_price': _money(purohit.base_price),
        'avg_rating': _money(purohit.avg_rating),
        'total_reviews': purohit.total_reviews,
        'total_bookings': purohit.total_bookings,
        'is_featured': bool(purohit.is_featured),
        'is_verified': bool(profile.is_verified) if profile else False,
        'verified_by_temple': (profile.verified_by_temple if profile else '') or '',
        'experience_years': profile.experience_years if profile else 0,
        'about': (profile.about if profile else '') or '',
        'languages': languages,
        'packages_count': purohit.puja_packages.count() if not include_packages else len(packages),
        'packages': packages,
        'offered_pujas': [
            pkg.puja.name
            for pkg in purohit.puja_packages.all()
            if getattr(pkg, 'puja', None) and pkg.puja.name
        ][:16],
        'accepts_travel_requests': bool(purohit.accepts_travel_requests),
        'travel_note': purohit.travel_note or '',
        'avatar_url': avatar,
        'work_start': purohit.work_start.strftime('%H:%M') if purohit.work_start else '06:00',
        'work_end': purohit.work_end.strftime('%H:%M') if purohit.work_end else '21:00',
        'gallery': gallery,
    }


def booking_payload(booking, request=None):
    package = booking.puja_package
    puja_name = package.puja.name if package and package.puja_id else 'Puja Ceremony'
    event_time = ''
    if booking.event_time:
        event_time = booking.event_time.strftime('%I:%M %p').lstrip('0')
    has_review = False
    if getattr(booking, 'review_id', None):
        has_review = True
    else:
        try:
            has_review = bool(getattr(booking, 'review', None))
        except Exception:
            has_review = False
    return {
        'id': booking.id,
        'booking_id': booking.booking_id,
        'purohit_id': booking.purohit_id,
        'purohit_name': booking.purohit.name if booking.purohit_id else 'Vedic Purohit',
        'purohit_slug': booking.purohit.slug if booking.purohit_id else '',
        'package_id': booking.puja_package_id,
        'puja_name': puja_name,
        'event_date': booking.event_date.isoformat() if booking.event_date else '',
        'event_time': event_time or 'Time TBD',
        'time_window': booking.get_time_window_label() if hasattr(booking, 'get_time_window_label') else event_time,
        'address': booking.address or '',
        'city': booking.city.name if booking.city_id else '',
        'city_id': booking.city_id,
        'area': booking.area.name if booking.area_id else '',
        'area_id': booking.area_id,
        'venue_type': booking.venue_type or '',
        'venue_label': booking.get_venue_label() if hasattr(booking, 'get_venue_label') else booking.venue_type,
        'needs_samagri': bool(booking.needs_samagri),
        'special_requests': booking.special_requests or '',
        'total_amount': _money(booking.total_amount),
        'advance_paid': _money(booking.advance_paid),
        'travel_fee': _money(booking.travel_fee),
        'status': booking.status,
        'payment_status': booking.payment_status,
        'lifecycle_key': booking.lifecycle_key,
        'lifecycle_label': booking.lifecycle_label,
        'reschedule_status': booking.reschedule_status,
        'suggested_date': booking.suggested_date.isoformat() if booking.suggested_date else '',
        'suggested_time': booking.suggested_time.strftime('%H:%M') if booking.suggested_time else '',
        'reschedule_reason': booking.reschedule_reason or '',
        'reschedule_count': booking.reschedule_count,
        'cancellation_reason': booking.cancellation_reason or '',
        'has_review': has_review,
        'created_at': booking.created_at.isoformat() if booking.created_at else '',
    }


def wallet_transaction_payload(txn):
    reason_label = txn.get_reason_display() if hasattr(txn, 'get_reason_display') else txn.reason
    return {
        'id': txn.id,
        'type': txn.transaction_type,
        'amount': _money(txn.amount),
        'reason': reason_label,
        'reason_code': txn.reason,
        'reference': txn.reference or '',
        'status': txn.status,
        'date': txn.created_at.strftime('%d %b %Y, %I:%M %p') if txn.created_at else '',
        'created_at': txn.created_at.isoformat() if txn.created_at else '',
    }


def notification_payload(item):
    return {
        'id': item.id,
        'title': item.title,
        'message': item.message,
        'link': item.link or '',
        'is_read': bool(item.is_read),
        'created_at': item.created_at.isoformat() if item.created_at else '',
        'date': item.created_at.strftime('%d %b, %I:%M %p') if item.created_at else '',
    }


def chat_message_payload(msg, current_user):
    return {
        'id': msg.id,
        'message': msg.message,
        'sender_id': msg.sender_id,
        'sender_name': msg.sender.get_full_name() or msg.sender.username,
        'is_mine': msg.sender_id == getattr(current_user, 'id', None),
        'is_read': bool(msg.is_read),
        'created_at': msg.created_at.isoformat() if msg.created_at else '',
        'time': msg.created_at.strftime('%I:%M %p') if msg.created_at else '',
    }


def travel_request_payload(item):
    preferred_time = ''
    if item.preferred_time:
        preferred_time = item.preferred_time.strftime('%H:%M')
    puja = None
    if item.puja_package_id and getattr(item, 'puja_package', None):
        puja = item.puja_package.puja
    return {
        'id': item.id,
        'request_id': item.request_id,
        'status': item.status,
        'status_label': item.get_status_display(),
        'purohit_id': item.purohit_id,
        'purohit_name': item.purohit.name if item.purohit_id else '',
        'package_id': item.puja_package_id,
        'puja_name': puja.name if puja else 'Visit request',
        'city': item.city.name if item.city_id else '',
        'area': item.area.name if item.area_id else '',
        'address': item.address or '',
        'venue_type': item.venue_type or '',
        'preferred_date': item.preferred_date.isoformat() if item.preferred_date else '',
        'preferred_time': preferred_time,
        'message': item.message or '',
        'purohit_response': item.purohit_response or '',
        'travel_fee': _money(item.travel_fee),
        'expires_at': item.expires_at.isoformat() if item.expires_at else '',
        'can_book': item.status == 'accepted' and bool(item.puja_package_id),
    }


def ticket_payload(ticket):
    return {
        'id': ticket.id,
        'ticket_id': ticket.ticket_id,
        'subject': ticket.subject,
        'description': ticket.description,
        'category': ticket.category,
        'status': ticket.status,
        'priority': ticket.priority,
        'created_at': ticket.created_at.isoformat() if ticket.created_at else '',
        'date': ticket.created_at.strftime('%d %b %Y') if ticket.created_at else '',
    }


def razorpay_order_payload(order):
    if not order:
        return None
    return {
        'id': order.get('id'),
        'amount': order.get('amount'),
        'currency': order.get('currency', getattr(settings, 'RAZORPAY_CURRENCY', 'INR')),
        'key': getattr(settings, 'RAZORPAY_KEY_ID', ''),
        'mock': bool(order.get('mock')) or str(order.get('id', '')).startswith('order_mock_'),
    }
