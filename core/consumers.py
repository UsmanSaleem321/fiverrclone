import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from core.models import Order, Message
from asgiref.sync import database_sync_to_async
from channels.layers import get_channel_layer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        
        # Check if the user is the buyer or seller of the order
        try:
            self.order = await database_sync_to_async(Order.objects.get)(id=self.order_id)
        except Order.DoesNotExist:
            return await self.close()

        if self.user != self.order.buyer and self.user != self.order.gig.seller:
            return await self.close()

        # Join the room group
        self.room_group_name = f"order_{self.order_id}_chat"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        content = text_data_json['content']

        # Save message to the database
        message = await database_sync_to_async(Message.objects.create)(
            order=self.order,
            sender=self.user,
            content=content
        )

        # Broadcast message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'content': message.content,
                'sender': message.sender.username,
                'timestamp': message.timestamp.isoformat()
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'content': event['content'],
            'sender': event['sender'],
            'timestamp': event['timestamp']
        }))
