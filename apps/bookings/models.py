import uuid
from django.db import models
from apps.core.models import TimeStampedModel, City, Area
from apps.accounts.models import CustomUser
from apps.purohits.models import Purohit
from apps.pujas.models import PurohitPujaPackage

class Booking(TimeStampedModel):
    STATUS_CHOICES = (
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Relationships
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings')
    purohit = models.ForeignKey(Purohit, on_delete=models.CASCADE, related_name='bookings')
    puja_package = models.ForeignKey(PurohitPujaPackage, on_delete=models.SET_NULL, null=True)
    
    # Event Details
    event_date = models.DateField()
    event_time = models.TimeField(null=True, blank=True)
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Reserved ritual duration for this booking (copied from puja at booking time).",
    )
    
    # Location
    address = models.TextField()
    city = models.ForeignKey(City, on_delete=models.PROTECT)
    area = models.ForeignKey(Area, on_delete=models.PROTECT)
    venue_type = models.CharField(
        max_length=20,
        blank=True,
        help_text="Where the ritual happens: home, temple, teerth, purohit, other.",
    )
    travel_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    travel_request = models.ForeignKey(
        'TravelRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings'
    )
    
    # Requirements
    needs_samagri = models.BooleanField(default=False)
    special_requests = models.TextField(blank=True)
    
    # Pricing
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    advance_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment Tracking
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    # Journey Milestones
    payment_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Reschedule Logic
    reschedule_requested_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='reschedule_requests')
    suggested_date = models.DateField(null=True, blank=True)
    suggested_time = models.TimeField(null=True, blank=True)
    RESCHEDULE_STATUS_CHOICES = [
        ('none', 'None'),
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    reschedule_status = models.CharField(max_length=20, choices=RESCHEDULE_STATUS_CHOICES, default='none')
    reschedule_requested_at = models.DateTimeField(null=True, blank=True)  # When purohit requested
    reschedule_accepted_at = models.DateTimeField(null=True, blank=True)   # When customer accepted
    reschedule_rejected_at = models.DateTimeField(null=True, blank=True)   # When customer rejected
    reschedule_count = models.IntegerField(default=0, help_text="Number of rescheduled occurrences")
    reschedule_reason = models.CharField(max_length=255, blank=True, help_text="Reason provided with the latest reschedule request")

    # Cancellation Logic
    cancellation_reason = models.TextField(blank=True, null=True)

    # Verification Codes
    start_code = models.CharField(max_length=10, blank=True)
    complete_code = models.CharField(max_length=10, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def save(self, *args, **kwargs):
        if not self.booking_id:
            # Generate a short unique ID like PC-HYD-A8B2
            short_uuid = str(uuid.uuid4()).split('-')[0][:4].upper()
            city_code = self.city.name[:3].upper() if self.city else 'IND'
            self.booking_id = f"PC-{city_code}-{short_uuid}"
            
            # Generate verification codes
            import random
            self.start_code = str(random.randint(1000, 9999))
            self.complete_code = str(random.randint(1000, 9999))
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.booking_id} - {self.customer.username} for {self.purohit.name}"

    def get_lifecycle_status(self):
        """
        Customer/purohit-facing lifecycle key + label.
        Confirmed means purohit accepted (accepted_at), not merely paid.
        """
        if self.status == 'cancelled':
            return 'cancelled', 'CANCELLED'
        if self.status == 'completed' or self.completed_at:
            return 'completed', 'COMPLETED'
        if self.started_at:
            return 'started', 'PUJA STARTED'
        if self.reschedule_status == 'pending':
            return 'reschedule_pending', 'RESCHEDULE PENDING'
        if self.payment_status != 'success':
            return 'awaiting_payment', 'AWAITING PAYMENT'
        if not self.accepted_at:
            return 'pending_confirmation', 'PENDING CONFIRMATION'
        return 'confirmed', 'CONFIRMED'

    @property
    def lifecycle_key(self):
        return self.get_lifecycle_status()[0]

    @property
    def lifecycle_label(self):
        return self.get_lifecycle_status()[1]

    def is_paid(self):
        return self.payment_status == 'success'

    def get_venue_label(self):
        from apps.bookings.location import venue_label
        return venue_label(self.venue_type)

    def get_duration_hours(self):
        """Reserved ritual length: booking snapshot → package → catalog default."""
        if self.duration_hours is not None:
            try:
                hours = float(self.duration_hours)
                if hours > 0:
                    return hours
            except (TypeError, ValueError):
                pass
        package = self.puja_package if self.puja_package_id else None
        if package is not None and hasattr(package, 'get_duration_hours'):
            return package.get_duration_hours()
        if package is not None and package.puja_id:
            try:
                return float(package.puja.base_duration_hours)
            except (TypeError, ValueError):
                pass
        return 2.0

    def get_buffer_minutes(self):
        package = self.puja_package if self.puja_package_id else None
        if package is not None and hasattr(package, 'get_buffer_minutes'):
            return package.get_buffer_minutes()
        return 30

    def get_event_end_time(self):
        """Estimated end time from start + reserved duration."""
        from datetime import datetime, timedelta, date
        if not self.event_time:
            return None
        hours = self.get_duration_hours()
        start_dt = datetime.combine(date.today(), self.event_time)
        return (start_dt + timedelta(hours=hours)).time()

    def get_time_window_label(self):
        if not self.event_time:
            return 'Time TBD'
        end = self.get_event_end_time()
        start_label = self.event_time.strftime('%H:%M')
        if not end:
            return start_label
        return f"{start_label} – {end.strftime('%H:%M')}"

    @property
    def reschedule_requested_by_customer(self):
        return bool(self.reschedule_requested_by_id and self.reschedule_requested_by_id == self.customer_id)

    @property
    def reschedule_requested_by_purohit(self):
        purohit_user_id = getattr(getattr(self.purohit, 'profile', None), 'user_id', None)
        return bool(self.reschedule_requested_by_id and purohit_user_id and self.reschedule_requested_by_id == purohit_user_id)


class BookingHistory(models.Model):
    EVENT_CHOICES = [
        ('status_change', 'Status Change'),
        ('reschedule_requested', 'Reschedule Requested'),
        ('reschedule_accepted', 'Reschedule Accepted'),
        ('reschedule_rejected', 'Reschedule Rejected'),
        ('reschedule_expired', 'Reschedule Expired'),
        ('cancellation', 'Cancellation'),
        ('payment_success', 'Payment Success'),
        ('ritual_started', 'Ritual Started'),
        ('ritual_completed', 'Ritual Completed'),
        ('code_generated', 'Verification Code Generated'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='history')
    event = models.CharField(max_length=30, choices=EVENT_CHOICES)
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    old_value = models.CharField(max_length=100, blank=True, help_text="Previous value for changes")
    new_value = models.CharField(max_length=100, blank=True, help_text="New value for changes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Booking Histories"
        indexes = [models.Index(fields=['booking', '-created_at'])]

    def __str__(self):
        return f"{self.booking.booking_id} - {self.event} at {self.created_at}"


class TravelRequest(TimeStampedModel):
    """Devotee asks a purohit to come to a place they do not already offer."""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('booked', 'Booked'),
    )

    request_id = models.CharField(max_length=24, unique=True, editable=False)
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='travel_requests')
    purohit = models.ForeignKey(Purohit, on_delete=models.CASCADE, related_name='travel_requests')
    puja_package = models.ForeignKey(PurohitPujaPackage, on_delete=models.SET_NULL, null=True, blank=True)

    city = models.ForeignKey(City, on_delete=models.PROTECT)
    area = models.ForeignKey(Area, on_delete=models.PROTECT)
    address = models.TextField()
    venue_type = models.CharField(max_length=20, blank=True)
    preferred_date = models.DateField()
    preferred_time = models.TimeField(null=True, blank=True)
    message = models.TextField(blank=True)

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    travel_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    purohit_response = models.CharField(max_length=240, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.request_id:
            short = str(uuid.uuid4()).split('-')[0][:4].upper()
            city_code = self.city.name[:3].upper() if self.city_id else 'IND'
            self.request_id = f'TR-{city_code}-{short}'
        super().save(*args, **kwargs)

    def is_open(self):
        from django.utils import timezone
        if self.status != 'accepted':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def matches_place(self, city, area, on_date):
        if not self.is_open() or not city or not area or not on_date:
            return False
        return self.city_id == city.id and self.area_id == area.id and self.preferred_date == on_date

    def __str__(self):
        return f'{self.request_id} ({self.status})'
