from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.message import MessageCreate, MessageUpdate, MessageResponse, MessageSearch
from app.crud.message import (
    create_message, get_message, get_room_messages,
    get_private_messages, search_messages,
    update_message, delete_message
)
from app.crud.room import is_room_admin, get_room
from app.models.user import User
from datetime import datetime, timezone

router = APIRouter(tags=["Messages"])


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        db_message = create_message(db, message, current_user.id)
        return db_message
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/messages", response_model=list[MessageResponse])
def read_messages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_room_messages(db, skip=skip, limit=limit)


@router.get("/messages/search", response_model=list[MessageResponse])
def search_messages_endpoint(
    q: str = Query(..., min_length=1, max_length=200),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = search_messages(db, query=q, user_id=current_user.id, skip=skip, limit=limit)
    return results


@router.put("/messages/{message_id}", response_model=MessageResponse)
def edit_message(
    message_id: int,
    message_update: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        db_message = update_message(db, message_id, current_user.id, message_update)
        if not db_message:
            raise HTTPException(status_code=404, detail="Message introuvable")
        return db_message
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/messages/{message_id}")
def remove_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_message = get_message(db, message_id)
    if not db_message:
        raise HTTPException(status_code=404, detail="Message introuvable")

    can_delete = (
        db_message.sender_id == current_user.id
        or current_user.is_admin
        or (db_message.room_id and is_room_admin(db, db_message.room_id, current_user.id))
    )
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que vos propres messages"
        )

    db_message.is_deleted = True
    db_message.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Message supprimé avec succès"}


@router.get("/rooms/{room_id}/messages", response_model=list[MessageResponse])
def read_room_messages(
    room_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_room_messages(db, room_id, skip=skip, limit=limit)


@router.post("/private-messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_private_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not message.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un message privé doit avoir un destinataire (receiver_id)"
        )
    try:
        db_message = create_message(db, message, current_user.id)
        return db_message
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/private-messages/{user_id}", response_model=list[MessageResponse])
def read_private_messages(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_private_messages(db, current_user.id, other_user_id=user_id, skip=skip, limit=limit)
