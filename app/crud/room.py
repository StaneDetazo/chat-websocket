from sqlalchemy.orm import Session
from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomCreate

def get_room(db: Session, room_id: int) -> Room | None:
    """
    Récupère un salon par son identifiant unique.
    """
    return db.query(Room).filter(Room.id == room_id).first()

def get_room_by_name(db: Session, name: str) -> Room | None:
    """
    Récupère un salon par son nom.
    """
    return db.query(Room).filter(Room.name == name).first()

def get_rooms(db: Session, skip: int = 0, limit: int = 100) -> list[Room]:
    """
    Liste tous les salons avec pagination.
    """
    return db.query(Room).offset(skip).limit(limit).all()

def create_room(db: Session, room: RoomCreate, creator_id: int) -> Room:
    """
    Crée un nouveau salon en base de données.
    Ajoute automatiquement son créateur à la liste des membres du salon.
    """
    # Vérifie la duplication par nom
    existing = get_room_by_name(db, room.name)
    if existing:
        raise ValueError("Room already exists")

    db_room = Room(
        name=room.name,
        description=room.description,
        created_by_id=creator_id
    )
    
    # Récupère l'utilisateur créateur et l'ajoute directement aux membres
    creator = db.query(User).filter(User.id == creator_id).first()
    if creator:
        db_room.members.append(creator)
        
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def delete_room(db: Session, room_id: int) -> bool:
    """
    Supprime un salon par son identifiant.
    Retourne True si la suppression a réussi, False sinon.
    """
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room:
        db.delete(db_room)
        db.commit()
        return True
    return False

def join_room(db: Session, room_id: int, user_id: int) -> bool:
    """
    Ajoute un utilisateur aux membres d'un salon (action Rejoindre).
    Retourne True si l'action a réussi (ou s'il y était déjà), False sinon.
    """
    db_room = db.query(Room).filter(Room.id == room_id).first()
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_room or not db_user:
        return "not_found"

    if db_user in db_room.members:
        return "already_member"

    db_room.members.append(db_user)
    db.commit()
    return "added"

def leave_room(db: Session, room_id: int, user_id: int) -> bool:
    """
    Retire un utilisateur de la liste des membres d'un salon (action Quitter).
    Retourne True si l'action a réussi, False sinon.
    """
    db_room = db.query(Room).filter(Room.id == room_id).first()
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_room or not db_user:
        return "not_found"

    if db_user not in db_room.members:
        return "not_member"

    db_room.members.remove(db_user)
    db.commit()
    return "left"

def get_room_members(db: Session, room_id: int) -> list[User]:
    """
    Récupère la liste de tous les utilisateurs membres d'un salon.
    """
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room:
        return db_room.members
    return None
