from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('package/<int:package_id>/', views.book_package, name='book'),
    path('package/<int:package_id>/request-travel/', views.request_travel, name='request_travel'),
    path('success/<str:booking_id>/', views.booking_success, name='success'),
    path('payment/verify/', views.verify_payment, name='verify_payment'),
    
    # Wallet and Razorpay payment
    path('payment/<str:booking_id>/', views.booking_payment, name='booking_payment'),
    path('payment/<str:booking_id>/verify/', views.verify_booking_payment, name='verify_booking_payment'),
]
