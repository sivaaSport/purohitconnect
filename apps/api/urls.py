from django.urls import path

from . import views
from . import workspace_views

app_name = 'api'

urlpatterns = [
    path('auth/send-otp/', views.send_otp, name='send_otp'),
    path('auth/verify-otp/', views.verify_otp, name='verify_otp'),
    path('auth/me/', views.me, name='me'),
    path('auth/logout/', views.logout, name='logout'),

    path('categories/', views.categories, name='categories'),
    path('pujas/', views.pujas, name='pujas'),
    path('cities/', views.cities, name='cities'),
    path('languages/', views.languages, name='languages'),
    path('purohits/', views.purohit_list, name='purohits'),
    path('purohits/<int:purohit_id>/', views.purohit_detail, name='purohit_detail'),
    path('purohits/<int:purohit_id>/slots/', views.purohit_slots, name='purohit_slots'),

    path('bookings/create/', views.create_booking, name='create_booking'),
    path('bookings/my/', views.my_bookings, name='my_bookings'),
    path('bookings/<str:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<str:booking_id>/pay/', views.booking_pay, name='booking_pay'),
    path('bookings/<str:booking_id>/verify-payment/', views.verify_booking_payment, name='verify_booking_payment'),
    path('bookings/<str:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('bookings/<str:booking_id>/reschedule/', views.booking_reschedule, name='booking_reschedule'),
    path('bookings/<str:booking_id>/reschedule/handle/', views.booking_reschedule_handle, name='booking_reschedule_handle'),
    path('bookings/<str:booking_id>/chat/', views.booking_chat, name='booking_chat'),
    path('bookings/<str:booking_id>/review/', views.booking_review, name='booking_review'),

    path('wallet/', views.wallet, name='wallet'),
    path('wallet/topup/', views.wallet_topup, name='wallet_topup'),
    path('wallet/verify-payment/', views.verify_wallet_payment, name='verify_wallet_payment'),

    path('travel-requests/', views.my_travel_requests, name='travel_requests'),

    path('notifications/', views.notifications, name='notifications'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='notifications_read_all'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='notification_read'),

    path('support/', views.support, name='support'),

    path('workspace/purohit/', workspace_views.purohit_dashboard, name='purohit_dashboard'),
    path('workspace/purohit/enable/', workspace_views.enable_purohit, name='purohit_enable'),
    path('workspace/purohit/bookings/', workspace_views.purohit_bookings, name='purohit_bookings'),
    path(
        'workspace/purohit/bookings/<str:booking_id>/status/',
        workspace_views.purohit_booking_status,
        name='purohit_booking_status',
    ),
    path('workspace/purohit/travel-requests/', workspace_views.purohit_travel_requests, name='purohit_travel_inbox'),
    path(
        'workspace/purohit/travel-requests/<int:request_pk>/respond/',
        workspace_views.purohit_travel_respond,
        name='purohit_travel_respond',
    ),
    path('workspace/purohit/packages/', workspace_views.purohit_packages, name='purohit_packages'),
    path('workspace/purohit/calendar/', workspace_views.purohit_calendar, name='purohit_calendar'),
]
