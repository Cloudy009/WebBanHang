from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import CustomUser  # Import mô hình người dùng tùy chỉnh
from .models import Room


@receiver(post_save, sender=CustomUser)
def create_user_room(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        # Tạo một room mới cho khách hàng
        room_name = f'{instance.username}_room'
        room = Room.objects.create(name=room_name, created_by=instance)
        
        # Thêm người dùng vào room
        room.users.add(instance)
