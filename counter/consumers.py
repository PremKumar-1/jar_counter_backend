# counter/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class JarCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('jar_counts', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('jar_counts', self.channel_name)

    async def receive(self, text_data):
        pass

    async def jar_count_update(self, event):
        jar_count = event['jar_count']
        await self.send(text_data=json.dumps({'jar_count': jar_count}))
