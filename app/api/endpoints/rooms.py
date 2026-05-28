from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.room import (
    RoomCreate, RoomResponse, RoomAdminResponse,
    AddMemberRequest, RemoveMemberRequest,
    PromoteAdminRequest, DemoteAdminRequest
)
from app.schemas.user import UserResponse
from app.schemas.warning import WarningCreate, WarningResponse
from app.crud.room import (
    get_room, get_rooms, create_room, delete_room,
    join_room, leave_room, get_room_members,
    is_room_admin, get_room_admins,
    add_room_member, remove_room_member,
    promote_room_admin, demote_room_admin
)
from app.crud.warning import create_warning
from app.models.user import User

router = APIRouter(prefix="/rooms", tags=["Salons"])


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_new_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        db_room = create_room(db=db, room=room, creator_id=current_user.id)
        resp = RoomResponse.model_validate(db_room)
        resp.member_count = len(db_room.members)
        resp.admin_ids = [a.user_id for a in db_room.admins]
        return resp
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un salon avec le nom '{room.name}' existe déjà"
        )


@router.get("/{room_id}", response_model=RoomResponse)
def read_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_room = get_room(db, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    resp = RoomResponse.model_validate(db_room)
    resp.member_count = len(db_room.members)
    resp.admin_ids = [a.user_id for a in db_room.admins]
    return resp


@router.get("/", response_model=list[RoomResponse])
def read_rooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rooms = get_rooms(db, skip=skip, limit=limit)
    result = []
    for room in rooms:
        r = RoomResponse.model_validate(room)
        r.member_count = len(room.members)
        r.admin_ids = [a.user_id for a in room.admins]
        result.append(r)
    return result


@router.delete("/{room_id}")
def remove_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin and not is_room_admin(db, room_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul un admin du salon ou un administrateur global peut supprimer ce salon"
        )
    success = delete_room(db, room_id)
    if not success:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    return {"message": "Salon supprimé avec succès"}


@router.post("/{room_id}/join")
def join_room_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    status_result = join_room(db, room_id, current_user.id)
    if status_result == "not_found":
        raise HTTPException(status_code=404, detail="Salon ou utilisateur introuvable")
    if status_result == "already_member":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vous êtes déjà membre de ce salon")
    return {"message": "Vous avez rejoint le salon avec succès"}


@router.post("/{room_id}/leave")
def leave_room_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    status_result = leave_room(db, room_id, current_user.id)
    if status_result == "not_found":
        raise HTTPException(status_code=404, detail="Salon ou utilisateur introuvable")
    if status_result == "not_member":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vous n'êtes pas membre de ce salon")
    return {"message": "Vous avez quitté le salon avec succès"}


@router.get("/{room_id}/members", response_model=list[UserResponse])
def room_members(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    members = get_room_members(db, room_id)
    if members is None:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    return members


@router.get("/{room_id}/admins", response_model=list[RoomAdminResponse])
def room_admins_list(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_room = get_room(db, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    return get_room_admins(db, room_id)


@router.post("/{room_id}/members")
def add_member(
    room_id: int,
    req: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    status_result = add_room_member(db, room_id, req.user_id, current_user.id)
    if status_result == "not_found":
        raise HTTPException(status_code=404, detail="Salon ou utilisateur introuvable")
    if status_result == "not_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas admin de ce salon")
    if status_result == "already_member":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cet utilisateur est déjà membre")
    return {"message": "Membre ajouté au salon avec succès"}


@router.delete("/{room_id}/members/{user_id}")
def remove_member(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    status_result = remove_room_member(db, room_id, user_id, current_user.id)
    if status_result == "not_found":
        raise HTTPException(status_code=404, detail="Salon ou utilisateur introuvable")
    if status_result == "not_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas admin de ce salon")
    if status_result == "not_member":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cet utilisateur n'est pas membre")
    if status_result == "cannot_remove_self":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez pas vous retirer vous-même")
    return {"message": "Membre retiré du salon avec succès"}


@router.post("/{room_id}/admins")
def promote_admin(
    room_id: int,
    req: PromoteAdminRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    status_result = promote_room_admin(db, room_id, req.user_id, current_user.id)
    if status_result == "not_found":
        raise HTTPException(status_code=404, detail="Salon ou utilisateur introuvable")
    if status_result == "not_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas admin de ce salon")
    if status_result == "not_member":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cet utilisateur doit d'abord être membre du salon")
    if status_result == "already_admin":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cet utilisateur est déjà admin")
    return {"message": "Utilisateur promu admin du salon avec succès"}


@router.delete("/{room_id}/admins/{user_id}")
def demote_admin(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    status_result = demote_room_admin(db, room_id, user_id, current_user.id)
    if status_result == "not_found":
        raise HTTPException(status_code=404, detail="Admin introuvable")
    if status_result == "not_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas admin de ce salon")
    if status_result == "cannot_demote_self":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez pas vous rétrograder vous-même")
    return {"message": "Admin rétrogradé avec succès"}


@router.post("/{room_id}/warnings", response_model=WarningResponse)
def warn_member(
    room_id: int,
    req: WarningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin and not is_room_admin(db, room_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul un admin du salon ou un administrateur global peut donner un avertissement"
        )
    try:
        warning = create_warning(
            db, user_id=req.user_id, given_by_id=current_user.id,
            reason=req.reason, room_id=room_id
        )
        return warning
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
