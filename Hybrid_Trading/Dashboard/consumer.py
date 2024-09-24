# dashboard/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.ticker = self.scope['url_route']['kwargs']['ticker']
        self.group_name = f'dashboard_{self.ticker}'

        # Join ticker group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave ticker group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive data from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        # Send message to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'dashboard_update',
                'message': message
            }
        )

    # Receive message from group
    async def dashboard_update(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))