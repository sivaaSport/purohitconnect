from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('support/', views.support_center, name='support'),
    path('support/ticket/create/', views.create_ticket, name='create_ticket'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/clear/', views.clear_all_notifications, name='clear_all_notifications'),
    path('notifications/count/', views.get_notifications_count, name='notifications_count'),
    path('notifications/list/', views.get_notifications_list, name='notifications_list'),
    path('notifications/<int:pk>/read/', views.mark_single_notification_read, name='mark_single_notification_read'),
    path('notifications/<int:pk>/delete/', views.delete_single_notification, name='delete_single_notification'),
]
