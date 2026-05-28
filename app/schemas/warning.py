from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class WarningCreate(BaseModel):
    user_id: int = Field(..., description="ID de l'utilisateur à avertir")
    room_id: int | None = Field(None, description="ID du salon concerné (optionnel)")
    reason: str = Field(..., min_length=1, max_length=500, description="Motif de l'avertissement")

class WarningResponse(BaseModel):
    id: int
    user_id: int
    room_id: int | None
    given_by_id: int
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
