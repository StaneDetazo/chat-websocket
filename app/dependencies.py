from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.security import decode_access_token
from app.models.user import User

# Définit le schéma OAuth2 avec le point de connexion de login pour l'interface Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db() -> Generator[Session, None, None]:
    """
    Dépendance fournissant une session de base de données SQLAlchemy par requête.
    Garantit la fermeture propre de la session après utilisation.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Dépendance vérifiant l'identité de l'utilisateur à partir du token JWT.
    Lève une HTTP 401 si le token est manquant, expiré ou invalide.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants de connexion",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Décode le jeton d'accès
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extrait l'username (clé 'sub') et l'ID utilisateur
    username: str | None = payload.get("sub")
    user_id: int | None = payload.get("user_id")
    
    if username is None or user_id is None:
        raise credentials_exception
    
    # Recherche l'utilisateur en base de données
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user
