"""Where a ritual is typically (or actually) performed."""

VENUE_HOME = 'home'
VENUE_TEMPLE = 'temple'
VENUE_TEERTH = 'teerth'
VENUE_PUROHIT = 'purohit'
VENUE_OTHER = 'other'

VENUE_CHOICES = [
    (VENUE_HOME, 'Devotee home'),
    (VENUE_TEMPLE, 'Temple'),
    (VENUE_TEERTH, 'Teerth / river / ghat'),
    (VENUE_PUROHIT, "Purohit's place"),
    (VENUE_OTHER, 'Other arranged venue'),
]

VENUE_LABELS = dict(VENUE_CHOICES)
VENUE_ICONS = {
    VENUE_HOME: 'house',
    VENUE_TEMPLE: 'landmark',
    VENUE_TEERTH: 'waves',
    VENUE_PUROHIT: 'user-round',
    VENUE_OTHER: 'map-pin',
}

VALID_VENUES = set(VENUE_LABELS)


def parse_venues(raw):
    if not raw:
        return []
    if isinstance(raw, (list, tuple)):
        values = raw
    else:
        values = str(raw).split(',')
    seen = []
    for value in values:
        code = str(value).strip()
        if code in VALID_VENUES and code not in seen:
            seen.append(code)
    return seen


def encode_venues(codes):
    return ','.join(parse_venues(codes))


def labeled_venues(codes):
    return [
        {'code': code, 'label': VENUE_LABELS[code], 'icon': VENUE_ICONS[code]}
        for code in parse_venues(codes)
    ]
