from django.urls import path
from . import views

app_name = 'pujas'

urlpatterns = [
    path('', views.puja_list, name='list'),
]
