from django.db import models
from django.utils.text import slugify
from apps.core.models import TimeStampedModel
from apps.purohits.models import Purohit
from .venues import encode_venues, labeled_venues, parse_venues


class PujaCategory(models.Model):
    """Household, Life Events, Festivals, Last Rites, Special Rituals"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, help_text="Lucide icon name")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Puja Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Puja(TimeStampedModel):
    """Platform ritual catalog entry (suggested defaults only)."""
    category = models.ForeignKey(PujaCategory, on_delete=models.CASCADE, related_name='pujas')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    base_duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Suggested typical duration. Each purohit sets their real duration on their package.",
    )
    typical_venues = models.CharField(
        max_length=80,
        blank=True,
        default='home',
        help_text="Comma-separated venue codes: home, temple, teerth, purohit, other.",
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.typical_venues = encode_venues(self.typical_venues) or 'home'
        super().save(*args, **kwargs)

    def get_typical_venues(self):
        return parse_venues(self.typical_venues) or ['home']

    def get_typical_venue_items(self):
        return labeled_venues(self.get_typical_venues())

    def __str__(self):
        return self.name


class PurohitPujaPackage(models.Model):
    """
    A purohit's offered ritual.

    Duration ownership:
    - Platform `Puja.base_duration_hours` = suggested default when adding
    - Package `duration_hours` = source of truth for booking slots
    - Booking stores a snapshot of duration at checkout
    """
    purohit = models.ForeignKey(Purohit, on_delete=models.CASCADE, related_name='puja_packages')
    puja = models.ForeignKey(Puja, on_delete=models.CASCADE, related_name='offered_by')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="How long this purohit needs for this ritual (hours).",
    )
    buffer_minutes = models.PositiveSmallIntegerField(
        default=30,
        help_text="Soft cushion after the ritual before the next booking can start.",
    )
    includes_samagri = models.BooleanField(default=False)
    samagri_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    custom_description = models.TextField(blank=True, help_text="Purohit's own description of how they perform it")
    venues = models.CharField(
        max_length=80,
        blank=True,
        help_text="Where this purohit performs the ritual. Empty falls back to catalog typical venues.",
    )
    venue_notes = models.CharField(
        max_length=240,
        blank=True,
        help_text="Optional place note, e.g. Trimbakeshwar only or I travel to Gaya.",
    )

    class Meta:
        unique_together = ('purohit', 'puja')

    def get_venues(self):
        codes = parse_venues(self.venues)
        if codes:
            return codes
        return self.puja.get_typical_venues()

    def get_venue_items(self):
        return labeled_venues(self.get_venues())

    def get_duration_hours(self) -> float:
        if self.duration_hours is not None:
            try:
                hours = float(self.duration_hours)
                if hours > 0:
                    return hours
            except (TypeError, ValueError):
                pass
        try:
            return float(self.puja.base_duration_hours)
        except (TypeError, ValueError, AttributeError):
            return 2.0

    def get_buffer_minutes(self) -> int:
        try:
            minutes = int(self.buffer_minutes)
            return minutes if minutes >= 0 else 30
        except (TypeError, ValueError):
            return 30

    def __str__(self):
        return f"{self.purohit.name} - {self.puja.name} ({self.price})"
