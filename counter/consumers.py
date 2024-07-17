import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class JarCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f"WebSocket connection accepted: {self.channel_name}")
        await self.channel_layer.group_add('jar_counts', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        logger.info(f"WebSocket connection closed: {self.channel_name}, code: {close_code}")
        await self.channel_layer.group_discard('jar_counts', self.channel_name)

    async def receive(self, text_data):
        logger.info(f"Received message: {text_data}")

    async def jar_count_update(self, event):
        jar_count = event['jar_count']
        await self.send(text_data=json.dumps({'jar_count': jar_count}))
