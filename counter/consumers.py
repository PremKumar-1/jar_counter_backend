import json
from channels.generic.websocket import AsyncWebsocketConsumer

class JarCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "jarcounts",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "jarcounts",
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Handle the received data if needed

    async def jar_count_update(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))
