import os
import django
import socketio
from django.core.asgi import get_asgi_application
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from app.models import Message, CustomUser  # Your app "app"

django_asgi_app = get_asgi_application()

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=getattr(settings, "SIO_CORS", ["*"]),
    logger=True,
    engineio_logger=True,
)

online_users = {}

logger = logging.getLogger(__name__)

@sio.event
async def connect(sid, environ, auth):
    print("✅ Socket.IO connected:", sid)

@sio.event
async def disconnect(sid):
    print("❌ Socket.IO disconnected:", sid)
    for emp, _sid in list(online_users.items()):
        if _sid == sid:
            online_users.pop(emp, None)
            await sio.emit("presence", {"employee_id": emp, "online": False})
            break

@sio.on("register")
async def register(sid, data):
    emp_id = str(data.get("employee_id"))
    if emp_id:
        online_users[emp_id] = sid
        await sio.emit("presence", {"employee_id": emp_id, "online": True})
        print(f"👤 Registered user {emp_id} with sid {sid}")

@sio.on("join_room")
async def join_room(sid, data):
    room = data.get("room")
    if room:
        await sio.enter_room(sid, room)
        print(f"📌 {sid} joined room {room}")

@sio.on("leave_room")
async def leave_room(sid, data):
    room = data.get("room")
    if room:
        await sio.leave_room(sid, room)
        print(f"🚪 {sid} left room {room}")

@sio.on("send_message")
async def send_message(sid, data):
    try:
        orig_room = data.get("room")
        sender_id = str(data.get("from"))
        text = data.get("text", "").strip()

        if not orig_room or not text:
            logger.warning("⚠️ Invalid message data: %s", data)
            return

        user_ids = orig_room.split(":")
        if len(user_ids) != 2:
            logger.warning("⚠️ Invalid room format: %s", orig_room)
            return

        user_ids.sort()
        room = ":".join(user_ids)

        receiver_id = user_ids[1] if user_ids[0] == sender_id else user_ids[0]

        sender = await sync_to_async(CustomUser.objects.get)(employee_id=sender_id)
        receiver = await sync_to_async(CustomUser.objects.get)(employee_id=receiver_id)

        await sync_to_async(Message.objects.create)(
            sender=sender,
            receiver=receiver,
            text=text,
            room=room,
            created_at=timezone.now()
        )
        logger.info("💾 Message saved: %s → %s: %s", sender_id, receiver_id, text[:50])

        await sio.emit("receive_message", {
            "room": room,
            "from": sender_id,
            "text": text,
            "timestamp": timezone.now().isoformat()
        }, room=room)
        logger.info("💬 Broadcasted message in room %s: %s", room, text[:50])
    except CustomUser.DoesNotExist:
        logger.error("❌ User not found: sender=%s or receiver=%s", sender_id, receiver_id)
    except Exception as e:
        logger.exception("❌ Failed to process send_message: %s", e)

@sio.on("call_user")
async def call_user(sid, data):
    callee = str(data.get("to"))
    target_sid = online_users.get(callee)
    if target_sid:
        await sio.emit("incoming_call", data, to=target_sid)

@sio.on("webrtc_offer")
async def webrtc_offer(sid, data):
    target_sid = online_users.get(str(data.get("to")))
    if target_sid:
        await sio.emit("webrtc_offer", data, to=target_sid)

@sio.on("webrtc_answer")
async def webrtc_answer(sid, data):
    target_sid = online_users.get(str(data.get("to")))
    if target_sid:
        await sio.emit("webrtc_answer", data, to=target_sid)

@sio.on("webrtc_ice_candidate")
async def webrtc_ice_candidate(sid, data):
    target_sid = online_users.get(str(data.get("to")))
    if target_sid:
        await sio.emit("webrtc_ice_candidate", data, to=target_sid)

@sio.on("end_call")
async def end_call(sid, data):
    target_sid = online_users.get(str(data.get("to")))
    if target_sid:
        await sio.emit("end_call", data, to=target_sid)

application = socketio.ASGIApp(
    sio,
    django_asgi_app,
    socketio_path="ws/socket.io",
)
