"""Purohit account / listing helpers."""
from django.utils.text import slugify

from apps.accounts.models import PurohitProfile
from apps.core.models import City
from apps.purohits.models import Purohit


def _display_name(user) -> str:
    name = (user.get_full_name() or user.username or 'Purohit').strip()
    if name.lower().startswith('pt.') or name.lower().startswith('pt '):
        return name
    return f'Pt. {name}'


def ensure_purohit_listing(user):
    """
    Ensure a purohit user has PurohitProfile + public listing.
    Signup only creates the profile; dashboard needs the listing.
    """
    if not user or getattr(user, 'role', None) != 'purohit':
        return None

    profile, _ = PurohitProfile.objects.get_or_create(user=user)

    try:
        return profile.purohit_listing
    except Purohit.DoesNotExist:
        pass

    city = user.city or City.objects.order_by('id').first()
    if city is None:
        return None

    name = _display_name(user)
    base_slug = slugify(f'{name}-{city.name}') or f'purohit-{user.pk}'
    slug = base_slug
    suffix = 1
    while Purohit.objects.filter(slug=slug).exists():
        suffix += 1
        slug = f'{base_slug}-{suffix}'

    listing = Purohit.objects.create(
        profile=profile,
        name=name,
        slug=slug,
        city=city,
    )
    from apps.bookings.location import ensure_home_offer
    ensure_home_offer(listing)
    return listing
