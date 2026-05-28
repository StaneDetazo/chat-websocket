from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone
from app.models.message import Message
from app.models.room import Room
from app.schemas.message import MessageCreate, MessageUpdate

MAX_MESSAGE_LENGTH = 2000

def create_message(db: Session, message: MessageCreate, sender_id: int) -> Message:
    if len(message.content) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Le message ne doit pas dépasser {MAX_MESSAGE_LENGTH} caractères")

    if message.room_id:
        room = db.query(Room).filter(Room.id == message.room_id).first()
        if not room:
            raise ValueError("Salon introuvable")
        if room.room_type.value == "readonly":
            raise ValueError("Ce salon est en lecture seule. Vous ne pouvez pas y écrire.")

    db_message = Message(
        sender_id=sender_id,
        room_id=message.room_id,
        receiver_id=message.receiver_id,
        content=message.content,
        is_private=message.receiver_id is not None
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_message(db: Session, message_id: int) -> Message | None:
    return db.query(Message).filter(Message.id == message_id).first()


def get_room_messages(
    db: Session, room_id: int, skip: int = 0, limit: int = 100
) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.room_id == room_id, Message.is_private == False)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_private_messages(
    db: Session, user_id: int, other_user_id: int | None = None,
    skip: int = 0, limit: int = 100
) -> list[Message]:
    query = db.query(Message).filter(
        Message.is_private == True,
        or_(
            Message.sender_id == user_id,
            Message.receiver_id == user_id
        )
    )
    if other_user_id:
        query = query.filter(
            or_(
                (Message.sender_id == user_id) & (Message.receiver_id == other_user_id),
                (Message.sender_id == other_user_id) & (Message.receiver_id == user_id)
            )
        )
    return query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()


def search_messages(
    db: Session, query: str, user_id: int | None = None,
    skip: int = 0, limit: int = 100
) -> list[Message]:
    db_query = db.query(Message).filter(
        Message.is_deleted == False,
        Message.content.ilike(f"%{query}%")
    )
    if user_id:
        db_query = db_query.filter(
            or_(
                Message.sender_id == user_id,
                Message.receiver_id == user_id,
                Message.room_id.in_(
                    db.query(Room.id).join(Room.members).filter(
                        Room.members.any(id=user_id)
                    )
                )
            )
        )
    return db_query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()


def update_message(db: Session, message_id: int, user_id: int, message_update: MessageUpdate) -> Message | None:
    db_message = db.query(Message).filter(Message.id == message_id).first()
    if not db_message:
        return None
    if db_message.sender_id != user_id:
        raise ValueError("Vous ne pouvez modifier que vos propres messages")
    if len(message_update.content) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Le message ne doit pas dépasser {MAX_MESSAGE_LENGTH} caractères")

    db_message.content = message_update.content
    db.commit()
    db.refresh(db_message)
    return db_message


def delete_message(db: Session, message_id: int, user_id: int) -> bool:
    db_message = db.query(Message).filter(Message.id == message_id).first()
    if not db_message:
        return False
    if db_message.sender_id != user_id:
        raise ValueError("Vous ne pouvez supprimer que vos propres messages")
    if db_message.is_deleted:
        raise ValueError("Ce message est déjà supprimé")

    db_message.is_deleted = True
    db_message.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True
