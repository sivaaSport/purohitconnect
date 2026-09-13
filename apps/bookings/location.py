"""Match a booking place to purohit-owned coverage or an accepted travel request."""

from apps.core.models import Area, City
from apps.pujas.venues import (
    VENUE_HOME,
    VENUE_PUROHIT,
    VENUE_TEMPLE,
    VENUE_LABELS,
    parse_venues,
)
from apps.purohits.models import PurohitServiceOffer


def _active_offers(purohit):
    return list(
        purohit.service_offers.filter(is_active=True).select_related('city', 'area')
    )


def covers(purohit, city, area, on_date, devotee=None):
    """True if this purohit already offers that place on that date, or accepted a request."""
    if not city or not on_date:
        return False
    for offer in _active_offers(purohit):
        if offer.covers_place(city, area) and offer.covers_date(on_date):
            return True
    if not _active_offers(purohit):
        if city.id == purohit.city_id:
            if not purohit.base_area_id or (area and area.id == purohit.base_area_id):
                return True
            if area and area.id in {a.id for a in purohit.service_areas.all()}:
                return True
    if devotee:
        request = matching_travel_request(purohit, devotee, city, area, on_date)
        if request:
            return True
    return False


def matching_travel_request(purohit, devotee, city, area, on_date):
    from apps.bookings.models import TravelRequest
    if not devotee or not devotee.is_authenticated or not city or not area or not on_date:
        return None
    for request in TravelRequest.objects.filter(
        purohit=purohit,
        customer=devotee,
        status='accepted',
        city=city,
        area=area,
        preferred_date=on_date,
    ):
        if request.is_open():
            return request
    return None


def upcoming_visits(purohit, today=None):
    from django.utils import timezone
    today = today or timezone.localdate()
    return [
        offer for offer in _active_offers(purohit)
        if offer.kind == PurohitServiceOffer.KIND_VISIT
        and offer.end_date
        and offer.end_date >= today
    ]


def served_areas(purohit, on_date=None):
    """Areas a devotee can book without a travel request (optionally on a date)."""
    offers = _active_offers(purohit)
    if on_date:
        offers = [offer for offer in offers if offer.covers_date(on_date)]
    else:
        from django.utils import timezone
        today = timezone.localdate()
        offers = [
            offer for offer in offers
            if offer.kind == PurohitServiceOffer.KIND_PERMANENT
            or (offer.end_date and offer.end_date >= today)
        ]
    areas = []
    seen = set()
    for offer in offers:
        if offer.area_id:
            if offer.area_id not in seen:
                areas.append(offer.area)
                seen.add(offer.area_id)
        else:
            for area in Area.objects.filter(city_id=offer.city_id).order_by('name'):
                if area.id not in seen:
                    areas.append(area)
                    seen.add(area.id)
    if areas:
        return areas
    if purohit.service_areas.exists():
        return list(purohit.service_areas.all().order_by('name'))
    if purohit.base_area_id:
        return [purohit.base_area]
    return list(Area.objects.filter(city_id=purohit.city_id).order_by('name'))


def served_area_ids(purohit, on_date=None):
    return {area.id for area in served_areas(purohit, on_date)}


def purohit_place_area(purohit):
    if purohit.base_area_id:
        return purohit.base_area
    areas = served_areas(purohit)
    return areas[0] if areas else None


def purohit_place_address(purohit):
    area = purohit_place_area(purohit)
    if area:
        return f"At purohit's place — {area.name}, {purohit.city.name}"
    return f"At purohit's place — {purohit.city.name}"


def coverage_summary(purohit, today=None):
    visits = upcoming_visits(purohit, today)
    permanents = [
        offer for offer in _active_offers(purohit)
        if offer.kind == PurohitServiceOffer.KIND_PERMANENT
    ]
    serve_labels = []
    for offer in permanents:
        label = offer.area.name if offer.area_id else f'{offer.city.name} (city-wide)'
        if label not in serve_labels:
            serve_labels.append(label)
    if not serve_labels:
        serve_labels = [area.name for area in served_areas(purohit)]
    return {
        'city_name': purohit.city.name,
        'base_label': purohit.base_area.name if purohit.base_area_id else purohit.city.name,
        'serves_labels': serve_labels,
        'visit_labels': [offer.label() for offer in visits],
        'travel_note': (getattr(purohit, 'travel_note', '') or '').strip(),
        'accepts_travel_requests': bool(getattr(purohit, 'accepts_travel_requests', True)),
    }


def _place_payload(offer):
    return {
        'cityId': offer.city_id,
        'areaId': offer.area_id or '',
        'cityName': offer.city.name,
        'areaName': offer.area.name if offer.area_id else '',
        'kind': offer.kind,
        'start': offer.start_date.isoformat() if offer.start_date else '',
        'end': offer.end_date.isoformat() if offer.end_date else '',
        'label': offer.label(),
    }


def coverage_payload(purohit):
    offers = _active_offers(purohit)
    permanents = [
        {'cityId': offer.city_id, 'areaId': offer.area_id}
        for offer in offers if offer.kind == PurohitServiceOffer.KIND_PERMANENT
    ]
    places = [_place_payload(offer) for offer in offers]
    if not permanents:
        if purohit.service_areas.exists():
            permanents = [
                {'cityId': area.city_id, 'areaId': area.id}
                for area in purohit.service_areas.all()
            ]
            if not places:
                places = [
                    {
                        'cityId': area.city_id,
                        'areaId': area.id,
                        'cityName': area.city.name,
                        'areaName': area.name,
                        'kind': 'permanent',
                        'start': '',
                        'end': '',
                        'label': f'{area.name}, {area.city.name} · always',
                    }
                    for area in purohit.service_areas.select_related('city').all()
                ]
        elif purohit.base_area_id:
            permanents = [{'cityId': purohit.city_id, 'areaId': purohit.base_area_id}]
        elif purohit.city_id:
            permanents = [{'cityId': purohit.city_id, 'areaId': None}]
        if not places and purohit.city_id:
            places = [{
                'cityId': purohit.city_id,
                'areaId': purohit.base_area_id or '',
                'cityName': purohit.city.name,
                'areaName': purohit.base_area.name if purohit.base_area_id else '',
                'kind': 'permanent',
                'start': '',
                'end': '',
                'label': (
                    f'{purohit.base_area.name}, {purohit.city.name} · always'
                    if purohit.base_area_id else f'{purohit.city.name} · always'
                ),
            }]
    return {
        'permanent': permanents,
        'visits': [
            {
                'cityId': offer.city_id,
                'areaId': offer.area_id or '',
                'start': offer.start_date.isoformat() if offer.start_date else '',
                'end': offer.end_date.isoformat() if offer.end_date else '',
            }
            for offer in offers if offer.kind == PurohitServiceOffer.KIND_VISIT
        ],
        'places': places,
        'acceptsTravel': bool(getattr(purohit, 'accepts_travel_requests', True)),
        'homeCityId': purohit.city_id,
        'purohitName': purohit.name,
    }


def areas_by_city_payload():
    payload = {}
    for area in Area.objects.select_related('city').order_by('city__name', 'name'):
        payload.setdefault(area.city_id, []).append({'id': area.id, 'name': area.name})
    return payload


def resolve_venue(package, raw_venue):
    venues = package.get_venues()
    venue = parse_venues([raw_venue or ''])
    venue = venue[0] if venue else ''
    if venue in venues:
        return venue
    if not venue and len(venues) == 1:
        return venues[0]
    if not venue and VENUE_HOME in venues:
        return VENUE_HOME
    return venue


def validate_booking_location(package, venue, city, area, address, on_date=None, devotee=None):
    """
    Return (ok, error, normalized).
    normalized includes venue_type, city, area, address, travel_request, travel_fee.
    """
    purohit = package.purohit
    venues = package.get_venues()
    venue = resolve_venue(package, venue)
    address = (address or '').strip()

    if venue not in venues:
        return False, 'Please choose a place this purohit offers for this ritual.', None

    if venue == VENUE_PUROHIT:
        locked_area = purohit_place_area(purohit)
        if not locked_area:
            return False, "This purohit has not set a base location yet.", None
        return True, '', {
            'venue_type': venue,
            'city': purohit.city,
            'area': locked_area,
            'address': purohit_place_address(purohit),
            'travel_request': None,
            'travel_fee': 0,
        }

    if not city or not area:
        return False, 'Please choose a city and area.', None
    if area.city_id != city.id:
        return False, 'That area is not in the selected city.', None
    if not address:
        hint = 'temple name' if venue == VENUE_TEMPLE else 'place details'
        if venue == VENUE_HOME:
            hint = 'home address'
        return False, f'Please enter the {hint}.', None
    if not on_date:
        return False, 'Please choose a date first so we can check where this purohit is offering services.', None

    travel_request = matching_travel_request(purohit, devotee, city, area, on_date)
    if covers(purohit, city, area, on_date, devotee=devotee):
        return True, '', {
            'venue_type': venue,
            'city': city,
            'area': area,
            'address': address,
            'travel_request': travel_request,
            'travel_fee': travel_request.travel_fee if travel_request else 0,
        }

    if getattr(purohit, 'accepts_travel_requests', True):
        return False, (
            'This purohit does not offer services at that place on that date. '
            'You can request a visit — they decide, and you pay only if they accept and you book.'
        ), None
    return False, 'This purohit is not offering services at that place on that date.', None


def venue_label(code):
    return VENUE_LABELS.get(code, '')


def location_form_context(package, on_date=None, devotee=None):
    purohit = package.purohit
    served = served_areas(purohit, on_date)
    place_area = purohit_place_area(purohit)
    payload = coverage_payload(purohit)
    return {
        'venue_options': [
            {'code': code, 'label': VENUE_LABELS[code]}
            for code in package.get_venues()
        ],
        'served_areas': served,
        'served_area_payload': [{'id': area.id, 'name': area.name} for area in served],
        'allows_destination': False,
        'purohit_place_area': place_area,
        'purohit_place_address': purohit_place_address(purohit),
        'travel_note': (getattr(purohit, 'travel_note', '') or '').strip(),
        'accepts_travel_requests': bool(getattr(purohit, 'accepts_travel_requests', True)),
        'package_venue_notes': (package.venue_notes or '').strip(),
        'cities': City.objects.all().order_by('name'),
        'offered_city_ids': {item['cityId'] for item in payload.get('places', [])},
        'areas_by_city': areas_by_city_payload(),
        'coverage': coverage_summary(purohit),
        'coverage_payload': payload,
        'upcoming_visits': upcoming_visits(purohit),
    }


def ensure_home_offer(purohit):
    if not purohit or not purohit.city_id:
        return None
    offer, _created = PurohitServiceOffer.objects.get_or_create(
        purohit=purohit,
        city=purohit.city,
        area=purohit.base_area,
        kind=PurohitServiceOffer.KIND_PERMANENT,
        defaults={'is_active': True},
    )
    return offer
