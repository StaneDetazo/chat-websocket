from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.crud.user import get_user, get_users, create_user, get_user_by_username

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    # Vérifie la duplication de username et renvoie un message clair
    existing = get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=409, detail=f"Le nom d'utilisateur '{user.username}' est déjà utilisé")

    return create_user(db=db, user=user)


@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id)

    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    return db_user


@router.get("/", response_model=list[UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_users(db, skip=skip, limit=limit)