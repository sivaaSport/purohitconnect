from collections import defaultdict

from django.db.models import Q
from django.shortcuts import render

from .catalog import category_sort_key
from .models import Puja, PujaCategory, PurohitPujaPackage
from .venues import VENUE_CHOICES, labeled_venues, parse_venues


def _attach_offered_venue_extras(pujas):
    """Show places some purohits added beyond the catalog usual venue."""
    offered = defaultdict(set)
    puja_ids = [puja.id for puja in pujas]
    if not puja_ids:
        return
    rows = (
        PurohitPujaPackage.objects.filter(puja_id__in=puja_ids)
        .exclude(venues='')
        .values_list('puja_id', 'venues')
    )
    for puja_id, raw in rows:
        offered[puja_id].update(parse_venues(raw))
    for puja in pujas:
        typical = set(puja.get_typical_venues())
        extra = {
            code for code in offered.get(puja.id, ())
            if code not in typical
        }
        puja.extra_offered_venue_items = labeled_venues(
            [code for code, _label in VENUE_CHOICES if code in extra]
        )


def puja_list(request):
    """List/search pujas, optionally filtered by category."""
    pujas = Puja.objects.select_related('category').all().order_by('name')

    query = (request.GET.get('q') or '').strip()
    category_slug = (request.GET.get('category') or '').strip()
    venue = parse_venues([request.GET.get('venue') or ''])
    venue = venue[0] if venue else ''

    if category_slug:
        pujas = pujas.filter(category__slug=category_slug)

    if venue:
        offered_ids = (
            PurohitPujaPackage.objects.filter(venues__icontains=venue)
            .values('puja_id')
        )
        pujas = pujas.filter(
            Q(typical_venues__icontains=venue) | Q(id__in=offered_ids)
        )

    if query:
        pujas = pujas.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    puja_rows = list(pujas)
    _attach_offered_venue_extras(puja_rows)

    categories = {}
    for puja in puja_rows:
        categories.setdefault(puja.category, []).append(puja)
    categories = dict(sorted(categories.items(), key=lambda item: category_sort_key(item[0])))

    all_categories = sorted(PujaCategory.objects.all(), key=category_sort_key)

    context = {
        'categories': categories,
        'search_query': query,
        'selected_category': category_slug,
        'selected_venue': venue,
        'venue_choices': VENUE_CHOICES,
        'all_categories': all_categories,
        'result_count': len(puja_rows),
    }
    return render(request, 'pujas/puja_list.html', context)
