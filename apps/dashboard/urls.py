from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('customer/', views.customer_dashboard, name='customer'),
    path('live/', views.dashboard_live_pulse, name='live_pulse'),
    path('purohit/', views.purohit_dashboard, name='purohit'),
    path('admin/support/', views.admin_support_dashboard, name='admin_support'),
    path('admin/payments/', views.admin_payment_dashboard, name='admin_payment'),
    path('admin/support/ticket/<str:ticket_id>/update/', views.update_ticket_status, name='update_ticket'),
    path('booking/<str:booking_id>/update/', views.update_booking_status, name='update_booking'),
    path('booking/<str:booking_id>/reschedule/request/', views.request_reschedule, name='request_reschedule'),
    path('booking/<str:booking_id>/reschedule/handle/', views.handle_reschedule, name='handle_reschedule'),
    path('booking/<str:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('availability/toggle/', views.toggle_availability, name='toggle_availability'),
    path('packages/manage/', views.manage_package, name='manage_package'),
    path('locations/update/', views.update_service_locations, name='update_service_locations'),
    path('travel-policy/update/', views.update_travel_policy, name='update_travel_policy'),
    path('offers/add/', views.add_service_offer, name='add_service_offer'),
    path('offers/<int:offer_pk>/delete/', views.delete_service_offer, name='delete_service_offer'),
    path('travel-requests/<int:request_pk>/respond/', views.respond_travel_request, name='respond_travel_request'),
    path('booking/<str:booking_id>/chat/', views.booking_chat, name='booking_chat'),
]
