from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.schemas.user import UserResponse

class RoomBase(BaseModel):
    """
    Schéma de base pour les informations communes des salons de discussion.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Nom du salon")
    description: str | None = Field(None, max_length=255, description="Description optionnelle du salon")

class RoomCreate(RoomBase):
    """
    Schéma pour la création d'un salon.
    """
    pass

class RoomResponse(RoomBase):
    """
    Schéma pour la réponse contenant les détails d'un salon.
    """
    id: int
    created_by_id: int
    created_at: datetime
    creator: UserResponse | None = None

    # Configuration pour permettre l'importation depuis un objet ORM (SQLAlchemy)
    model_config = ConfigDict(from_attributes=True)
