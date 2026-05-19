from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Self
from app.schemas.user import UserResponse

class MessageBase(BaseModel):
    """
    Schéma de base pour le contenu commun d'un message.
    """
    content: str = Field(..., min_length=1, description="Contenu textuel du message")

class MessageCreate(MessageBase):
    """
    Schéma pour la création d'un message.
    Valide qu'un message est destiné soit à un salon (room_id), soit à un utilisateur (receiver_id).
    """
    room_id: int | None = Field(None, description="Identifiant du salon ciblé (nullable)")
    receiver_id: int | None = Field(None, description="Identifiant de l'utilisateur privé ciblé (nullable)")

    @model_validator(mode="after")
    def validate_targets(self) -> Self:
        """
        Vérifie qu'exactement une destination est fournie (salon OU utilisateur).
        """
        if self.room_id is None and self.receiver_id is None:
            raise ValueError("Un message doit cibler soit un salon (room_id), soit un destinataire privé (receiver_id).")
        if self.room_id is not None and self.receiver_id is not None:
            raise ValueError("Un message ne peut pas cibler à la fois un salon et un destinataire privé.")
        return self

class MessageUpdate(MessageBase):
    """
    Schéma pour la modification du contenu d'un message existant.
    """
    pass

class MessageResponse(MessageBase):
    """
    Schéma pour la réponse contenant les détails d'un message.
    """
    id: int
    sender_id: int
    room_id: int | None
    receiver_id: int | None
    is_private: bool
    created_at: datetime
    updated_at: datetime
    sender: UserResponse | None = None

    # Configuration pour permettre l'importation depuis un objet ORM (SQLAlchemy)
    model_config = ConfigDict(from_attributes=True)
