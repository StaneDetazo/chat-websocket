from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from typing import Self
from app.schemas.user import UserResponse

MAX_MESSAGE_LENGTH = 2000

class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH, description="Contenu textuel du message")

class MessageCreate(MessageBase):
    room_id: int | None = Field(None, description="Identifiant du salon ciblé (nullable)")
    receiver_id: int | None = Field(None, description="Identifiant de l'utilisateur privé ciblé (nullable)")

    @model_validator(mode="after")
    def validate_targets(self) -> Self:
        if self.room_id is None and self.receiver_id is None:
            raise ValueError("Un message doit cibler soit un salon (room_id), soit un destinataire privé (receiver_id).")
        if self.room_id is not None and self.receiver_id is not None:
            raise ValueError("Un message ne peut pas cibler à la fois un salon et un destinataire privé.")
        return self

class MessageUpdate(MessageBase):
    pass

class MessageSearch(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, description="Terme de recherche")

class MessageResponse(MessageBase):
    id: int
    sender_id: int
    room_id: int | None
    receiver_id: int | None
    is_private: bool
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    sender: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def mask_deleted_content(self) -> Self:
        if self.is_deleted:
            self.content = "Ce message a été supprimé"
        return self
