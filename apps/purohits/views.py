from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from apps.core.models import City, Language
from apps.pujas.models import Puja
from .models import Purohit


def _positive_int(value):
    """Return int if value is a positive integer string, else None."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def purohit_list(request):
    """View to list and filter purohits using DB-backed discovery filters."""
    purohits = Purohit.objects.filter(is_active=True).select_related(
        'city', 'profile', 'profile__user', 'base_area'
    ).prefetch_related('profile__languages_spoken', 'puja_packages__puja', 'service_areas', 'service_offers')

    city_id = _positive_int(request.GET.get('city'))
    if city_id:
        from django.utils import timezone
        today = timezone.localdate()
        purohits = purohits.filter(
            Q(city_id=city_id)
            | Q(service_offers__is_active=True, service_offers__kind='permanent', service_offers__city_id=city_id)
            | Q(
                service_offers__is_active=True,
                service_offers__kind='visit',
                service_offers__city_id=city_id,
                service_offers__end_date__gte=today,
            )
        ).distinct()

    puja_id = _positive_int(request.GET.get('puja'))
    if puja_id:
        purohits = purohits.filter(puja_packages__puja_id=puja_id).distinct()

    language_id = _positive_int(request.GET.get('language'))
    if language_id:
        purohits = purohits.filter(profile__languages_spoken__id=language_id).distinct()

    query = (request.GET.get('q') or '').strip()
    if query:
        purohits = purohits.filter(
            Q(name__icontains=query)
            | Q(city__name__icontains=query)
            | Q(puja_packages__puja__name__icontains=query)
            | Q(profile__languages_spoken__name__icontains=query)
        ).distinct()

    purohit_rows = list(purohits)
    focus_puja = Puja.objects.filter(id=puja_id).first() if puja_id else None
    if focus_puja:
        for listing in purohit_rows:
            listing.matched_package = next(
                (pkg for pkg in listing.puja_packages.all() if pkg.puja_id == focus_puja.id),
                None,
            )

    context = {
        'purohits': purohit_rows,
        'pujas': Puja.objects.all().order_by('name'),
        'cities': City.objects.all().order_by('name'),
        'languages': Language.objects.all().order_by('name'),
        'selected_city': city_id,
        'selected_puja': puja_id,
        'selected_language': language_id,
        'search_query': query,
        'focus_puja': focus_puja,
    }

    if getattr(request, 'htmx', False):
        return render(request, 'purohits/partials/purohit_grid.html', context)

    return render(request, 'purohits/purohit_list.html', context)


def purohit_detail(request, slug):
    """View to show details of a specific purohit."""
    from django.utils import timezone
    from apps.purohits.utils import build_month_calendar

    purohit = get_object_or_404(
        Purohit.objects.select_related('city', 'profile', 'profile__user', 'base_area').prefetch_related('service_areas', 'service_offers'),
        slug=slug,
    )
    packages = list(purohit.puja_packages.select_related('puja', 'puja__category').all())
    focus_puja = Puja.objects.filter(id=_positive_int(request.GET.get('puja'))).first()
    focus_package = next((pkg for pkg in packages if focus_puja and pkg.puja_id == focus_puja.id), None)
    other_packages = [pkg for pkg in packages if not focus_package or pkg.id != focus_package.id]
    today = timezone.localdate()
    package_list = packages
    preview_duration = 2.0
    if focus_package:
        preview_duration = focus_package.get_duration_hours()
    elif package_list:
        preview_duration = max((p.get_duration_hours() for p in package_list), default=2.0)
    preview_weeks = build_month_calendar(
        purohit, today.year, today.month, duration_hours=preview_duration
    )
    gallery = list(purohit.gallery_media.all()[:24])

    context = {
        'purohit': purohit,
        'packages': packages,
        'focus_puja': focus_puja,
        'focus_package': focus_package,
        'other_packages': other_packages,
        'availability_weeks': preview_weeks,
        'availability_month_label': today.strftime('%B %Y'),
        'today': today,
        'gallery': gallery,
    }
    return render(request, 'purohits/purohit_detail.html', context)


def get_available_slots(request, slug):
    """HTMX partial: available ritual time windows for a date."""
    from datetime import datetime
    from apps.purohits.utils import get_day_slots, blocks_for_day, _as_float_hours

    purohit = get_object_or_404(Purohit, slug=slug)
    date_str = request.GET.get('date')
    duration_hours = _as_float_hours(request.GET.get('duration'))

    if not date_str:
        return render(request, 'purohits/partials/time_slots.html', {
            'slots': [],
            'available_count': 0,
            'day_fully_blocked': False,
            'duration_hours': duration_hours,
            'blocked_message': 'Select a date to see open timings.',
        })

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return HttpResponse('<div style="color:#FCA5A5;">Invalid date</div>')

    blocks = blocks_for_day(purohit, date_obj)
    day_fully_blocked = any(b.is_all_day for b in blocks)
    slots = [] if day_fully_blocked else get_day_slots(purohit, date_obj, duration_hours)
    available_count = sum(1 for s in slots if s['available'])

    return render(request, 'purohits/partials/time_slots.html', {
        'slots': slots,
        'available_count': available_count,
        'day_fully_blocked': day_fully_blocked,
        'duration_hours': duration_hours,
        'blocked_message': (blocks[0].blocked_reason if blocks else '') or 'Purohit is unavailable all day.',
        'required': True,
    })

