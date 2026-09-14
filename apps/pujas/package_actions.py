"""Purohit package add/update/delete shared by the website and /api/v1/."""

from decimal import Decimal, InvalidOperation

from apps.pujas.models import Puja, PurohitPujaPackage
from apps.pujas.venues import encode_venues


def _truthy(value):
    return value in (True, 'true', 'True', 'on', '1', 1)


def _venues_from(data):
    if hasattr(data, 'getlist'):
        raw = data.getlist('venues')
    else:
        raw = data.get('venues') if data is not None else None
    if raw is None:
        return ''
    if isinstance(raw, str):
        raw = raw.split(',')
    return encode_venues(raw)


def apply_package_action(*, purohit, action, data):
    """
    Return (ok, code, message, package_or_none).

    Codes: added, exists, updated, deleted, bad_price, bad_duration, bad_buffer,
    bad_samagri, missing_puja, missing_package, invalid.
    """
    action = (action or '').strip()
    data = data or {}

    if action == 'add':
        return _add_package(purohit, data)
    if action == 'update':
        return _update_package(purohit, data)
    if action == 'delete':
        return _delete_package(purohit, data)
    return False, 'invalid', 'Unknown package action.', None


def _parse_price(raw):
    try:
        price = Decimal(str(raw).strip())
        if price <= 0:
            raise InvalidOperation
        return price, None
    except (InvalidOperation, TypeError, ValueError):
        return None, (False, 'bad_price', 'Enter a valid price greater than zero.', None)


def _parse_duration(raw, fallback):
    try:
        duration_hours = Decimal(str(raw if raw not in (None, '') else fallback))
        if duration_hours <= 0 or duration_hours > 24:
            raise InvalidOperation
        return duration_hours, None
    except (InvalidOperation, TypeError, ValueError):
        return None, (False, 'bad_duration', 'Enter a valid ritual duration (hours).', None)


def _parse_buffer(raw):
    try:
        buffer_minutes = int(str(raw if raw not in (None, '') else '30').strip())
        if buffer_minutes < 0 or buffer_minutes > 180:
            raise ValueError
        return buffer_minutes, None
    except (TypeError, ValueError):
        return None, (False, 'bad_buffer', 'Buffer must be between 0 and 180 minutes.', None)


def _parse_samagri(includes, raw):
    if not includes or raw in (None, ''):
        return None, None
    try:
        return Decimal(str(raw).strip()), None
    except (InvalidOperation, TypeError, ValueError):
        return None, (False, 'bad_samagri', 'Enter a valid samagri price.', None)


def _add_package(purohit, data):
    puja_id = data.get('puja_id')
    if not puja_id:
        return False, 'missing_puja', 'Pick a ritual from the catalog.', None
    try:
        puja = Puja.objects.get(id=puja_id)
    except (Puja.DoesNotExist, ValueError, TypeError):
        return False, 'missing_puja', 'Pick a ritual from the catalog.', None
    venues = _venues_from(data)
    if not venues:
        venues = encode_venues(puja.get_typical_venues())
    includes = _truthy(data.get('includes_samagri'))
    price, err = _parse_price(data.get('price'))
    if err:
        return err
    duration_hours, err = _parse_duration(data.get('duration_hours'), puja.base_duration_hours)
    if err:
        return err
    buffer_minutes, err = _parse_buffer(data.get('buffer_minutes'))
    if err:
        return err
    samagri_price, err = _parse_samagri(includes, data.get('samagri_price'))
    if err:
        return err
    venue_notes = (data.get('venue_notes') or '').strip()[:240]
    custom_description = (data.get('custom_description') or '').strip()
    package, created = PurohitPujaPackage.objects.get_or_create(
        purohit=purohit,
        puja=puja,
        defaults={
            'price': price,
            'duration_hours': duration_hours,
            'buffer_minutes': buffer_minutes,
            'includes_samagri': includes,
            'samagri_price': samagri_price,
            'custom_description': custom_description,
            'venues': venues,
            'venue_notes': venue_notes,
        },
    )
    if not created:
        return False, 'exists', f'You already offer {puja.name}.', package
    return (
        True,
        'added',
        f'Added {puja.name} ({duration_hours}h + {buffer_minutes}m buffer) to your offerings.',
        package,
    )


def _get_owned_package(purohit, data):
    package_id = data.get('package_id')
    if not package_id:
        return None, (False, 'missing_package', 'Package is required.', None)
    try:
        return PurohitPujaPackage.objects.select_related('puja').get(id=package_id, purohit=purohit), None
    except (PurohitPujaPackage.DoesNotExist, ValueError, TypeError):
        return None, (False, 'missing_package', 'That offering was not found.', None)


def _update_package(purohit, data):
    package, err = _get_owned_package(purohit, data)
    if err:
        return err
    includes = _truthy(data.get('includes_samagri'))
    price, err = _parse_price(data.get('price'))
    if err:
        return err
    duration_hours, err = _parse_duration(data.get('duration_hours'), package.get_duration_hours())
    if err:
        return err
    buffer_minutes, err = _parse_buffer(data.get('buffer_minutes'))
    if err:
        return err
    samagri_price, err = _parse_samagri(includes, data.get('samagri_price'))
    if err:
        return err
    venues = _venues_from(data) or encode_venues(package.get_venues())
    package.price = price
    package.duration_hours = duration_hours
    package.buffer_minutes = buffer_minutes
    package.includes_samagri = includes
    package.samagri_price = samagri_price
    package.custom_description = (data.get('custom_description') or '').strip()
    package.venues = venues
    package.venue_notes = (data.get('venue_notes') or '').strip()[:240]
    package.save()
    return True, 'updated', f'Updated {package.puja.name} ({duration_hours}h ritual).', package


def _delete_package(purohit, data):
    package, err = _get_owned_package(purohit, data)
    if err:
        return err
    name = package.puja.name
    package.delete()
    return True, 'deleted', f'Removed {name} from your offerings.', None
