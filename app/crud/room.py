from sqlalchemy.orm import Session
from app.models.room import Room, RoomAdmin, RoomType, room_members
from app.models.user import User
from app.schemas.room import RoomCreate


def get_room(db: Session, room_id: int) -> Room | None:
    return db.query(Room).filter(Room.id == room_id).first()


def get_room_by_name(db: Session, name: str) -> Room | None:
    return db.query(Room).filter(Room.name == name).first()


def get_rooms(db: Session, skip: int = 0, limit: int = 100) -> list[Room]:
    return db.query(Room).offset(skip).limit(limit).all()


def get_rooms_for_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Room]:
    return (
        db.query(Room)
        .outerjoin(room_members, (room_members.c.room_id == Room.id) & (room_members.c.user_id == user_id))
        .filter(
            (Room.room_type != RoomType.PRIVATE) | (room_members.c.user_id.isnot(None))
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_room(db: Session, room: RoomCreate, creator_id: int) -> Room:
    existing = get_room_by_name(db, room.name)
    if existing:
        raise ValueError("Room already exists")

    db_room = Room(
        name=room.name,
        description=room.description,
        room_type=room.room_type,
        created_by_id=creator_id
    )

    creator = db.query(User).filter(User.id == creator_id).first()
    if creator:
        db_room.members.append(creator)

    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    room_admin = RoomAdmin(room_id=db_room.id, user_id=creator_id, promoted_by_id=creator_id)
    db.add(room_admin)
    db.commit()

    return db_room


def delete_room(db: Session, room_id: int) -> bool:
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room:
        db.delete(db_room)
        db.commit()
        return True
    return False


def join_room(db: Session, room_id: int, user_id: int) -> str:
    db_room = db.query(Room).filter(Room.id == room_id).first()
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_room or not db_user:
        return "not_found"
    if db_user in db_room.members:
        return "already_member"

    db_room.members.append(db_user)
    db.commit()
    return "added"


def leave_room(db: Session, room_id: int, user_id: int) -> str:
    db_room = db.query(Room).filter(Room.id == room_id).first()
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_room or not db_user:
        return "not_found"
    if db_user not in db_room.members:
        return "not_member"

    db_room.members.remove(db_user)
    db.query(RoomAdmin).filter(
        RoomAdmin.room_id == room_id, RoomAdmin.user_id == user_id
    ).delete()
    db.commit()
    return "left"


def get_room_members(db: Session, room_id: int) -> list[User] | None:
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room:
        return db_room.members
    return None


def is_room_admin(db: Session, room_id: int, user_id: int) -> bool:
    return db.query(RoomAdmin).filter(
        RoomAdmin.room_id == room_id, RoomAdmin.user_id == user_id
    ).first() is not None


def get_room_admins(db: Session, room_id: int) -> list[RoomAdmin]:
    return db.query(RoomAdmin).filter(RoomAdmin.room_id == room_id).all()


def add_room_member(db: Session, room_id: int, user_id: int, requester_id: int) -> str:
    db_room = db.query(Room).filter(Room.id == room_id).first()
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_room or not db_user:
        return "not_found"
    if not is_room_admin(db, room_id, requester_id):
        return "not_admin"
    if db_user in db_room.members:
        return "already_member"

    db_room.members.append(db_user)
    db.commit()
    return "added"


def remove_room_member(db: Session, room_id: int, user_id: int, requester_id: int) -> str:
    db_room = db.query(Room).filter(Room.id == room_id).first()
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_room or not db_user:
        return "not_found"
    if not is_room_admin(db, room_id, requester_id):
        return "not_admin"
    if db_user not in db_room.members:
        return "not_member"
    if user_id == requester_id:
        return "cannot_remove_self"

    db_room.members.remove(db_user)
    db.query(RoomAdmin).filter(
        RoomAdmin.room_id == room_id, RoomAdmin.user_id == user_id
    ).delete()
    db.commit()
    return "removed"


def promote_room_admin(db: Session, room_id: int, user_id: int, requester_id: int) -> str:
    if not is_room_admin(db, room_id, requester_id):
        return "not_admin"

    db_user = db.query(User).filter(User.id == user_id).first()
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room or not db_user:
        return "not_found"
    if db_user not in db_room.members:
        return "not_member"
    if is_room_admin(db, room_id, user_id):
        return "already_admin"

    admin = RoomAdmin(room_id=room_id, user_id=user_id, promoted_by_id=requester_id)
    db.add(admin)
    db.commit()
    return "promoted"


def demote_room_admin(db: Session, room_id: int, user_id: int, requester_id: int) -> str:
    if not is_room_admin(db, room_id, requester_id):
        return "not_admin"
    if not is_room_admin(db, room_id, user_id):
        return "not_admin"
    if user_id == requester_id:
        return "cannot_demote_self"

    db.query(RoomAdmin).filter(
        RoomAdmin.room_id == room_id, RoomAdmin.user_id == user_id
    ).delete()
    db.commit()
    return "demoted"
