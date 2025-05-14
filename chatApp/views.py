# chatapp/views.py
from django.shortcuts import get_object_or_404, render
from .models import Room
from accounts.models import CustomUser

def room_list(request):
    if request.user.is_staff:
        rooms = Room.objects.all()
    else:
        rooms = Room.objects.filter(users=request.user)
    return render(request, 'chatApp/room_list.html', {'rooms': rooms})

def room(request, room_name):
    return render(request, 'chatApp/room.html', {'room_name': room_name})

# chatApp/views.py

from rest_framework import generics
from .models import Message
from API.serializers import MessageSerializer

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        room_name = self.kwargs['room_name']
        return Message.objects.filter(room__name=room_name).order_by('-timestamp')[:100]  # Tải 100 tin nhắn mới nhất

#Test

from django.http import JsonResponse
from chatApp.models import Room, Message

def get_rooms(request):
    rooms = Room.objects.all()
    room_list = [{'name': room.name} for room in rooms]
    return JsonResponse({'rooms': room_list})

def load_room(request, room_name):
    room = Room.objects.get(name=room_name)
    messages = Message.objects.filter(room=room).order_by('-timestamp')[:20]
    message_list = [{
        'user': msg.user.username,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages]
    return JsonResponse({'messages': message_list})

def messbox(request):
    if request.user.is_staff:
        rooms = Room.objects.all()
    else:
        rooms = Room.objects.filter(users=request.user)
    return render(request, 'chatApp/messbox.html')
