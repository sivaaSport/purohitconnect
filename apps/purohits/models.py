from django.db import models
from django.utils.text import slugify
from datetime import time
from apps.core.models import TimeStampedModel, City, Area
from apps.accounts.models import PurohitProfile


class Purohit(TimeStampedModel):
    profile = models.OneToOneField(PurohitProfile, on_delete=models.CASCADE, related_name='purohit_listing')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='purohits')
    base_area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, related_name='purohits_based_here')
    service_areas = models.ManyToManyField(Area, related_name='serviced_by_purohits', blank=True)
    travel_note = models.CharField(
        max_length=240,
        blank=True,
        help_text="Shown when you accept travel requests, e.g. I come if devotee covers train + stay.",
    )
    accepts_travel_requests = models.BooleanField(
        default=True,
        help_text="Allow devotees to request a visit when you do not already offer their location.",
    )

    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=1100.00,
        help_text="Starting price for basic pujas",
    )

    # Bookable day window — purohit can accept defaults or extend for long rituals
    work_start = models.TimeField(
        default=time(6, 0),
        help_text="Earliest bookable start time on open days.",
    )
    work_end = models.TimeField(
        default=time(21, 0),
        help_text="Latest bookable end time on open days.",
    )

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.IntegerField(default=0)
    total_bookings = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.city.name}")
        super().save(*args, **kwargs)

    def get_served_areas(self):
        from apps.bookings.location import served_areas
        return served_areas(self)

    def get_coverage_summary(self):
        from apps.bookings.location import coverage_summary
        return coverage_summary(self)

    def get_work_window(self):
        start = self.work_start or time(6, 0)
        end = self.work_end or time(21, 0)
        if end <= start:
            end = time(21, 0)
        return start, end

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class PurohitMedia(models.Model):
    """Photos or videos of past pujas / ceremonies for a purohit profile gallery."""
    MEDIA_TYPES = (
        ('photo', 'Photo'),
        ('video', 'Video'),
    )

    purohit = models.ForeignKey(Purohit, on_delete=models.CASCADE, related_name='gallery_media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='photo')
    file = models.FileField(upload_to='purohit_gallery/%Y/%m/')
    title = models.CharField(max_length=120, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name_plural = 'Purohit gallery media'

    def __str__(self):
        return self.title or f"{self.media_type} · {self.purohit.name}"


class PurohitAvailability(models.Model):
    """
    A blocked window for a purohit.
    - start_time/end_time both null => full-day block
    - otherwise blocks only that time range on `date`
    Multiple timed blocks per day are allowed.
    """
    purohit = models.ForeignKey(Purohit, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_available = models.BooleanField(default=False, help_text="False means blocked/unavailable")
    blocked_reason = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Purohit Availabilities"
        ordering = ['date', 'start_time']

    @property
    def is_all_day(self):
        return self.start_time is None and self.end_time is None

    def label(self):
        if self.is_all_day:
            return 'All day'
        start = self.start_time.strftime('%H:%M') if self.start_time else '—'
        end = self.end_time.strftime('%H:%M') if self.end_time else '—'
        return f'{start} – {end}'

    def __str__(self):
        status = 'Available' if self.is_available else 'Blocked'
        return f"{self.purohit.name} - {self.date} {self.label()} ({status})"


class PurohitServiceOffer(models.Model):
    """A place this purohit chooses to work — always, or for a dated visit."""

    KIND_PERMANENT = 'permanent'
    KIND_VISIT = 'visit'
    KIND_CHOICES = (
        (KIND_PERMANENT, 'Permanent'),
        (KIND_VISIT, 'Temporary visit'),
    )

    purohit = models.ForeignKey(Purohit, on_delete=models.CASCADE, related_name='service_offers')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='purohit_service_offers')
    area = models.ForeignKey(
        Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='purohit_service_offers'
    )
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_PERMANENT)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=240, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['kind', 'city__name', 'area__name', '-start_date']

    def covers_date(self, on_date):
        if not self.is_active:
            return False
        if self.kind == self.KIND_PERMANENT:
            return True
        if not on_date or not self.start_date or not self.end_date:
            return False
        return self.start_date <= on_date <= self.end_date

    def covers_place(self, city, area=None):
        if not self.is_active or not city:
            return False
        if self.city_id != city.id:
            return False
        if self.area_id is None:
            return True
        return bool(area and area.id == self.area_id)

    def place_label(self):
        if self.area_id and self.city_id:
            return f'{self.area.name}, {self.city.name}'
        if self.city_id:
            return self.city.name
        return self.area.name if self.area_id else 'Unknown place'

    def label(self):
        place = self.place_label()
        if self.kind == self.KIND_VISIT and self.start_date and self.end_date:
            return f'{place} · {self.start_date:%d %b}–{self.end_date:%d %b}'
        return f'{place} · always'

    def __str__(self):
        return f'{self.purohit.name} — {self.label()}'
