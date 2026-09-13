from django.urls import path
from . import views

app_name = 'purohits'

urlpatterns = [
    path('', views.purohit_list, name='list'),
    path('<slug:slug>/', views.purohit_detail, name='detail'),
    path('<slug:slug>/available-slots/', views.get_available_slots, name='available_slots'),
]
