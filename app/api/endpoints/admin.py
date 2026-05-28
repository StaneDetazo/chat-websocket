from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.schemas.room import RoomCreate, RoomResponse
from app.schemas.warning import WarningCreate, WarningResponse
from app.crud.room import get_room, get_rooms, create_room, delete_room, get_room_members
from app.crud.user import get_user, get_users
from app.crud.warning import create_warning, get_user_warnings, get_room_warnings
from app.models.user import User
from app.models.room import Room

router = APIRouter(prefix="/admin", tags=["Administration"])


def check_admin(current_user: User):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    return current_user


@router.get("/users", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    return get_users(db, skip=skip, limit=limit)


@router.post("/users/{user_id}/suspend")
def suspend_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas suspendre votre propre compte")
    user.is_active = False
    db.commit()
    return {"message": f"L'utilisateur '{user.username}' a été suspendu"}


@router.post("/users/{user_id}/reactivate")
def reactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_active = True
    db.commit()
    return {"message": f"L'utilisateur '{user.username}' a été réactivé"}


@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room_admin(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    try:
        return create_room(db=db, room=room, creator_id=current_user.id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un salon avec le nom '{room.name}' existe déjà"
        )


@router.get("/rooms", response_model=list[RoomResponse])
def list_rooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    rooms = get_rooms(db, skip=skip, limit=limit)
    result = []
    for room in rooms:
        r = RoomResponse.model_validate(room)
        r.member_count = len(room.members)
        r.admin_ids = [a.user_id for a in room.admins]
        result.append(r)
    return result


@router.delete("/rooms/{room_id}")
def remove_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    success = delete_room(db, room_id)
    if not success:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    return {"message": "Salon supprimé avec succès"}


@router.post("/warnings", response_model=WarningResponse)
def warn_user(
    req: WarningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    try:
        warning = create_warning(
            db, user_id=req.user_id, given_by_id=current_user.id,
            reason=req.reason, room_id=req.room_id
        )
        return warning
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/warnings/user/{user_id}", response_model=list[WarningResponse])
def list_user_warnings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    return get_user_warnings(db, user_id)


@router.get("/warnings/room/{room_id}", response_model=list[WarningResponse])
def list_room_warnings(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    return get_room_warnings(db, room_id)
