from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.schemas.user import UserResponse
from app.models.room import RoomType
from typing import Self

class RoomBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Nom du salon")
    description: str | None = Field(None, max_length=255, description="Description optionnelle du salon")
    room_type: RoomType = Field(RoomType.PUBLIC, description="Type de salon: public, private, readonly")

class RoomCreate(RoomBase):
    pass

class RoomAdminResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    promoted_by_id: int | None
    created_at: datetime
    user: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)

class RoomResponse(RoomBase):
    id: int
    created_by_id: int
    created_at: datetime
    creator: UserResponse | None = None
    member_count: int = 0
    admin_ids: list[int] = []

    model_config = ConfigDict(from_attributes=True)

class AddMemberRequest(BaseModel):
    user_id: int = Field(..., description="ID de l'utilisateur à ajouter")

class RemoveMemberRequest(BaseModel):
    user_id: int = Field(..., description="ID de l'utilisateur à retirer")

class PromoteAdminRequest(BaseModel):
    user_id: int = Field(..., description="ID de l'utilisateur à promouvoir admin")

class DemoteAdminRequest(BaseModel):
    user_id: int = Field(..., description="ID de l'utilisateur à rétrograder")
