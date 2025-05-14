from django.conf import settings
from django.db import models

# Create your models here.
from accounts.models import CustomUser

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    users = models.ManyToManyField(CustomUser, related_name='rooms')
    created_by = models.ForeignKey(CustomUser, related_name='created_rooms', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'

    class Meta:
        db_table = 'message'
