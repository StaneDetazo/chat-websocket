import json
import time
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.security import decode_access_token
from app.models.user import User
from app.models.room import Room, RoomType
from app.crud.message import create_message, MAX_MESSAGE_LENGTH
from app.schemas.message import MessageCreate

RATE_LIMIT_MESSAGES = 10
RATE_LIMIT_WINDOW = 10

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
        self.user_connections: dict[int, list[WebSocket]] = {}
        self.room_connections: dict[int, dict[int, list[WebSocket]]] = {}
        self.user_message_times: dict[int, list[float]] = defaultdict(list)

    def _check_rate_limit(self, user_id: int) -> bool:
        now = time.time()
        times = self.user_message_times[user_id]
        times = [t for t in times if now - t < RATE_LIMIT_WINDOW]
        self.user_message_times[user_id] = times
        if len(times) >= RATE_LIMIT_MESSAGES:
            return False
        times.append(now)
        return True

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            self.user_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.user_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        for room_id in list(self.room_connections.keys()):
            if user_id in self.room_connections[room_id]:
                if websocket in self.room_connections[room_id][user_id]:
                    self.room_connections[room_id][user_id].remove(websocket)
                if not self.room_connections[room_id][user_id]:
                    del self.room_connections[room_id][user_id]
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]

    def join_room_ws(self, room_id: int, user_id: int, websocket: WebSocket):
        if room_id not in self.room_connections:
            self.room_connections[room_id] = {}
        if user_id not in self.room_connections[room_id]:
            self.room_connections[room_id][user_id] = []
        self.room_connections[room_id][user_id].append(websocket)

    def leave_room_ws(self, room_id: int, user_id: int, websocket: WebSocket):
        if room_id in self.room_connections and user_id in self.room_connections[room_id]:
            if websocket in self.room_connections[room_id][user_id]:
                self.room_connections[room_id][user_id].remove(websocket)
            if not self.room_connections[room_id][user_id]:
                del self.room_connections[room_id][user_id]
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]

    async def broadcast_to_room(self, room_id: int, message: dict, exclude_user_id: int | None = None):
        if room_id not in self.room_connections:
            return
        for user_id, connections in list(self.room_connections[room_id].items()):
            if exclude_user_id and user_id == exclude_user_id:
                continue
            for ws in connections:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    async def send_private_message(self, receiver_id: int, message: dict):
        if receiver_id not in self.user_connections:
            return
        for ws in self.user_connections[receiver_id]:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def send_to_user(self, user_id: int, message: dict):
        if user_id not in self.user_connections:
            return
        for ws in self.user_connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


def get_user_from_token(token: str, db: Session) -> User | None:
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user


async def handle_websocket_main(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token d'authentification manquant")
        return

    db = SessionLocal()
    try:
        user = get_user_from_token(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token invalide ou expiré")
            return

        if not user.is_active:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Votre compte a été suspendu. Contactez un administrateur."
            )
            return

        await manager.connect(websocket, user.id)

        await manager.send_to_user(user.id, {
            "event": "connected",
            "message": f"Bienvenue {user.username}! Vous êtes connecté au chat temps réel."
        })

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    await manager.send_to_user(user.id, {
                        "event": "error",
                        "message": "Format JSON invalide"
                    })
                    continue

                event = message_data.get("event")
                if not event:
                    await manager.send_to_user(user.id, {
                        "event": "error",
                        "message": "Champ 'event' requis"
                    })
                    continue

                if event == "join_room":
                    room_id = message_data.get("room_id")
                    if not room_id:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Champ 'room_id' requis pour rejoindre un salon"
                        })
                        continue

                    room = db.query(Room).filter(Room.id == room_id).first()
                    if not room:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Salon introuvable"
                        })
                        continue

                    if user not in room.members:
                        room.members.append(user)
                        db.commit()

                    manager.join_room_ws(room_id, user.id, websocket)
                    await manager.send_to_user(user.id, {
                        "event": "join_room",
                        "room_id": room_id,
                        "message": f"Vous avez rejoint le salon '{room.name}'"
                    })
                    await manager.broadcast_to_room(room_id, {
                        "event": "user_joined",
                        "room_id": room_id,
                        "user_id": user.id,
                        "username": user.username,
                        "message": f"{user.username} a rejoint le salon"
                    }, exclude_user_id=user.id)

                elif event == "leave_room":
                    room_id = message_data.get("room_id")
                    if room_id:
                        room = db.query(Room).filter(Room.id == room_id).first()
                        if room and user in room.members:
                            room.members.remove(user)
                            db.commit()
                        manager.leave_room_ws(room_id, user.id, websocket)
                        await manager.broadcast_to_room(room_id, {
                            "event": "user_left",
                            "room_id": room_id,
                            "user_id": user.id,
                            "username": user.username,
                            "message": f"{user.username} a quitté le salon"
                        })

                elif event == "message":
                    room_id = message_data.get("room_id")
                    content = message_data.get("content", "").strip()

                    if not room_id or not content:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Champs 'room_id' et 'content' requis"
                        })
                        continue

                    if not manager._check_rate_limit(user.id):
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Trop de messages envoyés. Veuillez attendre quelques secondes."
                        })
                        continue

                    room = db.query(Room).filter(Room.id == room_id).first()
                    if not room:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Salon introuvable"
                        })
                        continue

                    if room.room_type == RoomType.READONLY:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Ce salon est en lecture seule. Vous ne pouvez pas y écrire."
                        })
                        continue

                    if len(content) > MAX_MESSAGE_LENGTH:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": f"Le message ne doit pas dépasser {MAX_MESSAGE_LENGTH} caractères"
                        })
                        continue

                    try:
                        msg_create = MessageCreate(room_id=room_id, content=content)
                        db_message = create_message(db, msg_create, user.id)
                    except ValueError as e:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": str(e)
                        })
                        continue

                    await manager.broadcast_to_room(room_id, {
                        "event": "message",
                        "room_id": room_id,
                        "message_id": db_message.id,
                        "sender_id": user.id,
                        "sender_username": user.username,
                        "content": content,
                        "created_at": db_message.created_at.isoformat()
                    })

                elif event == "private_message":
                    receiver_id = message_data.get("receiver_id")
                    content = message_data.get("content", "").strip()

                    if not receiver_id or not content:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Champs 'receiver_id' et 'content' requis"
                        })
                        continue

                    if not manager._check_rate_limit(user.id):
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Trop de messages envoyés. Veuillez attendre quelques secondes."
                        })
                        continue

                    if len(content) > MAX_MESSAGE_LENGTH:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": f"Le message ne doit pas dépasser {MAX_MESSAGE_LENGTH} caractères"
                        })
                        continue

                    receiver = db.query(User).filter(User.id == receiver_id).first()
                    if not receiver:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Destinataire introuvable"
                        })
                        continue

                    if not receiver.is_active:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": "Ce compte a été suspendu. Impossible d'envoyer un message."
                        })
                        continue

                    try:
                        msg_create = MessageCreate(receiver_id=receiver_id, content=content)
                        db_message = create_message(db, msg_create, user.id)
                    except ValueError as e:
                        await manager.send_to_user(user.id, {
                            "event": "error",
                            "message": str(e)
                        })
                        continue

                    msg_payload = {
                        "event": "private_message",
                        "message_id": db_message.id,
                        "sender_id": user.id,
                        "sender_username": user.username,
                        "content": content,
                        "created_at": db_message.created_at.isoformat()
                    }

                    await manager.send_to_user(user.id, {
                        **msg_payload,
                        "receiver_id": receiver_id,
                        "receiver_username": receiver.username
                    })

                    await manager.send_private_message(receiver_id, {
                        **msg_payload,
                        "receiver_id": receiver_id,
                        "receiver_username": receiver.username
                    })

                else:
                    await manager.send_to_user(user.id, {
                        "event": "error",
                        "message": f"Événement inconnu: '{event}'"
                    })

        except WebSocketDisconnect:
            pass
        finally:
            for room_id in list(manager.room_connections.keys()):
                manager.leave_room_ws(room_id, user.id, websocket)
            manager.disconnect(websocket, user.id)
    finally:
        db.close()
