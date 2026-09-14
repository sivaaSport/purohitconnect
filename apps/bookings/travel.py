"""Create a devotee travel request. Shared by the website and /api/v1/."""

from apps.bookings.location import covers, resolve_venue
from apps.bookings.models import TravelRequest
from apps.core.models import Notification
from apps.pujas.venues import VENUE_PUROHIT


def submit_travel_request(
    *,
    customer,
    package,
    city,
    area,
    address,
    venue_type,
    preferred_date,
    preferred_time=None,
    message='',
):
    """
    Return (ok, code, message, travel_request).

    Codes: created, already_open, already_covers, own_listing, not_accepting,
    invalid_place, missing_address, purohit_venue.
    """
    purohit = package.purohit
    listing_user_id = getattr(getattr(purohit, 'profile', None), 'user_id', None)
    if listing_user_id and listing_user_id == customer.id:
        return False, 'own_listing', 'You cannot request a visit from your own listing.', None
    if not getattr(purohit, 'accepts_travel_requests', True):
        return False, 'not_accepting', 'This purohit is not accepting travel requests.', None

    venue_type = resolve_venue(package, venue_type)
    address = (address or '').strip()
    message = (message or '').strip()

    if not city or not area or area.city_id != city.id:
        return False, 'invalid_place', 'Please choose a city and area.', None
    if not address:
        return False, 'missing_address', 'Please enter the place details.', None
    if venue_type == VENUE_PUROHIT:
        return (
            False,
            'purohit_venue',
            "A travel request is only needed when the ritual is not at the purohit's place.",
            None,
        )
    if covers(purohit, city, area, preferred_date, devotee=customer):
        return (
            False,
            'already_covers',
            'This purohit already offers that place on that date. You can book directly.',
            None,
        )

    existing = TravelRequest.objects.filter(
        customer=customer,
        purohit=purohit,
        city=city,
        area=area,
        preferred_date=preferred_date,
        status='pending',
    ).first()
    if existing:
        return (
            True,
            'already_open',
            f'You already have an open request ({existing.request_id}). The purohit will respond there.',
            existing,
        )

    travel_request = TravelRequest.objects.create(
        customer=customer,
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
    purohit_user = getattr(getattr(purohit, 'profile', None), 'user', None)
    if purohit_user:
        Notification.objects.create(
            user=purohit_user,
            title='Travel request',
            message=(
                f"{customer.get_full_name() or customer.username} asked you to come to "
                f"{area.name}, {city.name} on {preferred_date:%d %b} for {package.puja.name}."
            ),
            link='/dashboard/purohit/#travel-requests',
        )
    return (
        True,
        'created',
        f'Visit request {travel_request.request_id} sent. You pay only if they accept and you book.',
        travel_request,
    )


def respond_travel_request(*, purohit, travel_request, decision, travel_fee=0, purohit_response=''):
    """
    Return (ok, code, message).

    Codes: accepted, declined, already_answered, bad_fee, invalid_decision.
    """
    from datetime import timedelta
    from decimal import Decimal, InvalidOperation
    from django.utils import timezone

    if travel_request.purohit_id != purohit.id:
        return False, 'forbidden', 'That travel request is not for this listing.'
    if travel_request.status != 'pending':
        return False, 'already_answered', 'That travel request has already been answered.'

    travel_request.purohit_response = (purohit_response or '').strip()[:240]
    choice = (decision or '').strip().lower()
    if choice == 'accept':
        try:
            fee = Decimal(str(travel_fee or 0))
        except (InvalidOperation, TypeError, ValueError):
            return False, 'bad_fee', 'Enter a valid travel fee, or leave it at 0.'
        if fee < 0:
            return False, 'bad_fee', 'Travel fee cannot be negative.'
        travel_request.status = 'accepted'
        travel_request.travel_fee = fee
        travel_request.expires_at = timezone.now() + timedelta(hours=48)
        travel_request.save()
        book_link = '/dashboard/customer/'
        if travel_request.puja_package_id:
            book_link = f'/bookings/package/{travel_request.puja_package_id}/?request={travel_request.request_id}'
        Notification.objects.create(
            user=travel_request.customer,
            title='Travel request accepted',
            message=(
                f"{purohit.name} can come to {travel_request.area.name} on "
                f"{travel_request.preferred_date:%d %b}."
                + (f" Travel fee: ₹{fee}." if fee else "")
                + " Book within 48 hours to lock it in."
            ),
            link=book_link,
        )
        return True, 'accepted', f'Accepted {travel_request.request_id}. The devotee can book now.'
    if choice == 'decline':
        travel_request.status = 'declined'
        travel_request.save()
        Notification.objects.create(
            user=travel_request.customer,
            title='Travel request declined',
            message=(
                f"{purohit.name} cannot take the visit to {travel_request.area.name} "
                f"on {travel_request.preferred_date:%d %b}."
            ),
            link='/dashboard/customer/',
        )
        return True, 'declined', f'Declined {travel_request.request_id}.'
    return False, 'invalid_decision', 'Choose accept or decline.'

