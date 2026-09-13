from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('write/<str:booking_id>/', views.write_review, name='write'),
]
