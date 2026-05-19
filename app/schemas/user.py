from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class UserBase(BaseModel):
    """
    Schéma de base pour les informations communes de l'utilisateur.
    """
    username: str = Field(..., min_length=3, max_length=50, description="Nom d'utilisateur")

class UserCreate(UserBase):
    """
    Schéma pour la création d'un utilisateur (inscription).
    """
    password: str = Field(..., min_length=6, max_length=100, description="Mot de passe en clair")

class UserResponse(UserBase):
    """
    Schéma pour la réponse contenant les détails d'un utilisateur.
    """
    id: int
    created_at: datetime

    # Configuration pour permettre l'importation depuis un objet ORM (SQLAlchemy)
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """
    Schéma pour la réponse contenant le token JWT d'authentification.
    """
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """
    Schéma pour les données encodées dans le token JWT.
    """
    username: str | None = None
    user_id: int | None = None
