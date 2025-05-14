import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import Message, Room
from django.utils import timezone

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def websocket_connect(self, event):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.last_message_timestamp = timezone.now()  # Initialize timestamp for messages

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')
        message_content = text_data_json.get('message')
        user = self.scope['user']

        if not isinstance(user, User):
            return

        if action == 'load_old_messages':
            oldest_message_timestamp = text_data_json.get('oldest_message_timestamp')
            old_messages = await self.get_old_messages(oldest_message_timestamp)
            await self.send(text_data=json.dumps({
                'type': 'old_messages',
                'messages': old_messages
            }))
        else:
            await self.save_message(user, message_content)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'user': user.username,
                    'timestamp': timezone.now().isoformat()  # Include timestamp for sorting
                }
            )

    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'user': user,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def save_message(self, user, message_content):
        room, created = Room.objects.get_or_create(name=self.room_name)
        return Message.objects.create(
            room=room,
            user=user,
            content=message_content
        )
    
    # @database_sync_to_async
    # def get_old_messages(self, oldest_message_timestamp=None):
    #     room = Room.objects.get(name=self.room_name)
    #     if oldest_message_timestamp:
    #         # Ensure the timestamp is in a format that can be compared
    #         oldest_message_timestamp = timezone.parse_datetime(oldest_message_timestamp)
    #         messages = Message.objects.filter(room=room, timestamp__lt=oldest_message_timestamp).order_by('-timestamp')[:20]
    #     else:
    #         messages = Message.objects.filter(room=room).order_by('-timestamp')[:20]

    #     return [{
    #         'user': message.user.username,
    #         'content': message.content,
    #         'timestamp': message.timestamp.isoformat()
    #     } for message in messages]

    @database_sync_to_async
    def get_old_messages(self, oldest_message_timestamp=None):
        room = Room.objects.get(name=self.room_name)
        if oldest_message_timestamp:
            messages = Message.objects.filter(room=room, timestamp__lt=oldest_message_timestamp).order_by('-timestamp')[:20]
        else:
            messages = Message.objects.filter(room=room).order_by('-timestamp')[:20]

        return [{
            'user': message.user.username,
            'content': message.content,
            'timestamp': message.timestamp.isoformat()
        } for message in messages]




# class ChatConsumer(AsyncWebsocketConsumer):
#     async def websocket_connect(self, event):
#         self.room_name = self.scope['url_route']['kwargs']['room_name']
#         self.room_group_name = f'chat_{self.room_name}'

#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()

#     async def websocket_disconnect(self, event):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         action = text_data_json.get('action')
#         message_content = text_data_json.get('message')
#         user = self.scope['user']

#         if not isinstance(user, User):
#             return

#         if action == 'load_old_messages':
#             # Load old messages from the database
#             messages = await self.get_old_messages()
#             await self.send(text_data=json.dumps({
#                 'type': 'old_messages',
#                 'messages': messages
#             }))
#         else:
#             # Save new message to the database
#             await self.save_message(user, message_content)

#             # Send message to room group
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'chat_message',
#                     'message': message_content,
#                     'user': user.username
#                 }
#             )

#     async def chat_message(self, event):
#         message = event['message']
#         user = event['user']

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({
#             'type': 'chat_message',
#             'message': message,
#             'user': user
#         }))

#     @database_sync_to_async
#     def save_message(self, user, message_content):
#         room, created = Room.objects.get_or_create(name=self.room_name)
#         return Message.objects.create(
#             room=room,
#             user=user,
#             content=message_content
#         )

#     @database_sync_to_async
#     def get_old_messages(self):
#         room = Room.objects.get(name=self.room_name)
#         messages = Message.objects.filter(room=room).order_by('-timestamp')[:20]  # Adjust number as needed
#         return [{
#             'user': message.user.username,
#             'content': message.content,
#             'timestamp': message.timestamp.isoformat()  # Include timestamp
#         } for message in messages]

