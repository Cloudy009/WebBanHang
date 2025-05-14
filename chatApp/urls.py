# chatapp/urls.py
from django.urls import path
from . import views

app_name = 'chatapp'

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('room/<str:room_name>/', views.room, name='room'),
    path('messbox/', views.messbox, name='messbox'),
    path('rooms/', views.get_rooms, name='get_rooms'),
    path('load_room/<str:room_name>/', views.load_room, name='load_room'),
]
