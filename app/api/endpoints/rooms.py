from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.room import RoomCreate, RoomResponse
from app.crud.room import (
    get_room,
    get_rooms,
    create_room,
    delete_room,
    join_room,
    leave_room,
    get_room_members
)

router = APIRouter(prefix="/rooms", tags=["Rooms"])


# CREATE ROOM
@router.post("/", response_model=RoomResponse)
def create_new_room(
    room: RoomCreate,
    creator_id: int,
    db: Session = Depends(get_db)
):
    try:
        return create_room(db=db, room=room, creator_id=creator_id)
    except ValueError:
        raise HTTPException(status_code=409, detail=f"Un salon avec le nom '{room.name}' existe déjà")


# GET ONE ROOM
@router.get("/{room_id}", response_model=RoomResponse)
def read_room(room_id: int, db: Session = Depends(get_db)):
    db_room = get_room(db, room_id)

    if not db_room:
        raise HTTPException(status_code=404, detail="Room introuvable")

    return db_room


# GET ALL ROOMS
@router.get("/", response_model=list[RoomResponse])
def read_rooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return get_rooms(db, skip=skip, limit=limit)


# DELETE ROOM
@router.delete("/{room_id}")
def remove_room(room_id: int, db: Session = Depends(get_db)):
    success = delete_room(db, room_id)

    if not success:
        raise HTTPException(status_code=404, detail="Room introuvable")

    return {"message": "Room supprimé avec succès"}


# JOIN ROOM
@router.post("/{room_id}/join")
def join_room_endpoint(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    status = join_room(db, room_id, user_id)

    if status == "not_found":
        raise HTTPException(status_code=404, detail="Salon ou utilisateur introuvable")
    if status == "already_member":
        raise HTTPException(status_code=409, detail="L'utilisateur est déjà membre du salon")

    return {"message": "Utilisateur ajouté au salon"}


# LEAVE ROOM
@router.post("/{room_id}/leave")
def leave_room_endpoint(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    status = leave_room(db, room_id, user_id)

    if status == "not_found":
        raise HTTPException(status_code=404, detail="Salon ou utilisateur introuvable")
    if status == "not_member":
        raise HTTPException(status_code=409, detail="L'utilisateur n'est pas membre du salon")

    return {"message": "Utilisateur retiré du salon"}


# GET MEMBERS
@router.get("/{room_id}/members")
def room_members(room_id: int, db: Session = Depends(get_db)):
    members = get_room_members(db, room_id)
    if members is None:
        raise HTTPException(status_code=404, detail="Salon introuvable")

    return members