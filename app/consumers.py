import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # We'll create a room name per user session for simplicity
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()  # Reject anonymous users
        else:
            # Group name for this user to receive messages
            self.room_group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            message = data.get("message")
            receiver_id = data.get("room")  # room = user_id of receiver

            # Send message to receiver group
            await self.channel_layer.group_send(
                f"user_{receiver_id}",
                {
                    "type": "chat.message",
                    "message": message,
                    "sender_id": self.user.id,
                    "sender_name": self.user.get_full_name() or self.user.username,
                }
            )

            # Optionally, echo back to sender
            await self.send(text_data=json.dumps({
                "message": message,
                "sender_id": self.user.id,
                "sender_name": "You",
            }))

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender": event["sender_name"],
        }))
