from django.contrib import admin
from .models import Booking, BookingHistory, TravelRequest


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer', 'purohit', 'event_date', 'status', 'reschedule_status', 'total_amount')
    list_filter = ('status', 'reschedule_status', 'event_date', 'payment_status', 'city', 'needs_samagri')
    search_fields = ('booking_id', 'customer__username', 'purohit__name', 'customer__phone')
    readonly_fields = ('booking_id', 'start_code', 'complete_code', 'created_at', 'updated_at')
    date_hierarchy = 'event_date'
    fieldsets = (
        ('Booking Info', {
            'fields': ('booking_id', 'customer', 'purohit', 'puja_package', 'status')
        }),
        ('Event Details', {
            'fields': ('event_date', 'event_time', 'venue_type', 'address', 'city', 'area')
        }),
        ('Pricing & Requirements', {
            'fields': ('total_amount', 'advance_paid', 'travel_fee', 'travel_request', 'needs_samagri', 'special_requests')
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_at', 'razorpay_order_id', 'razorpay_payment_id')
        }),
        ('Journey Milestones', {
            'fields': ('accepted_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Verification Codes', {
            'fields': ('start_code', 'complete_code'),
        }),
        ('Reschedule', {
            'fields': ('reschedule_status', 'reschedule_requested_by', 'reschedule_requested_at',
                      'suggested_date', 'suggested_time', 'reschedule_reason',
                      'reschedule_accepted_at', 'reschedule_rejected_at', 'reschedule_count'),
            'classes': ('collapse',)
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = ('booking', 'event', 'user', 'created_at')
    list_filter = ('event', 'created_at')
    search_fields = ('booking__booking_id', 'message', 'user__username')
    readonly_fields = ('booking', 'event', 'user', 'message', 'old_value', 'new_value', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        return False  # History is auto-generated, no manual addition
    
    def has_delete_permission(self, request, obj=None):
        return False  # Maintain audit trail integrity


@admin.register(TravelRequest)
class TravelRequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'purohit', 'customer', 'city', 'area', 'preferred_date', 'status', 'travel_fee')
    list_filter = ('status', 'city', 'preferred_date')
    search_fields = ('request_id', 'purohit__name', 'customer__username', 'address')
    readonly_fields = ('request_id', 'created_at', 'updated_at')
