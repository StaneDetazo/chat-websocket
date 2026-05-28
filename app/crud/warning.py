from sqlalchemy.orm import Session
from app.models.warning import Warning
from app.models.user import User
from app.models.room import Room


def create_warning(
    db: Session, user_id: int, given_by_id: int,
    reason: str, room_id: int | None = None
) -> Warning:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("Utilisateur introuvable")

    if room_id:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise ValueError("Salon introuvable")

    db_warning = Warning(
        user_id=user_id,
        room_id=room_id,
        given_by_id=given_by_id,
        reason=reason
    )
    db.add(db_warning)
    db.commit()
    db.refresh(db_warning)
    return db_warning


def get_user_warnings(db: Session, user_id: int) -> list[Warning]:
    return db.query(Warning).filter(Warning.user_id == user_id).order_by(
        Warning.created_at.desc()
    ).all()


def get_room_warnings(db: Session, room_id: int) -> list[Warning]:
    return db.query(Warning).filter(Warning.room_id == room_id).order_by(
        Warning.created_at.desc()
    ).all()
