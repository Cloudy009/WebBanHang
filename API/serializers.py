# your_app/serializers.py

from rest_framework import serializers
from home.models import Review
from chatApp.models import Message

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'  # Hoặc bạn có thể chỉ định các trường cụ thể

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'room', 'user', 'content', 'timestamp']