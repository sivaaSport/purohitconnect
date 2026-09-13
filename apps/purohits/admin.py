from django.contrib import admin
from .models import Purohit, PurohitAvailability, PurohitMedia, PurohitServiceOffer


@admin.register(Purohit)
class PurohitAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'base_price', 'is_active', 'is_featured', 'avg_rating')
    list_filter = ('city', 'is_active', 'is_featured')
    search_fields = ('name', 'profile__user__email', 'profile__user__phone')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('service_areas',)


@admin.register(PurohitAvailability)
class PurohitAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('purohit', 'date', 'start_time', 'end_time', 'is_available', 'blocked_reason')
    list_filter = ('is_available', 'date')
    search_fields = ('purohit__name',)
    date_hierarchy = 'date'


@admin.register(PurohitMedia)
class PurohitMediaAdmin(admin.ModelAdmin):
    list_display = ('purohit', 'media_type', 'title', 'is_featured', 'created_at')
    list_filter = ('media_type', 'is_featured')
    search_fields = ('purohit__name', 'title', 'caption')


@admin.register(PurohitServiceOffer)
class PurohitServiceOfferAdmin(admin.ModelAdmin):
    list_display = ('purohit', 'kind', 'city', 'area', 'start_date', 'end_date', 'is_active')
    list_filter = ('kind', 'is_active', 'city')
    search_fields = ('purohit__name', 'city__name', 'area__name', 'note')
