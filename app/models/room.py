from sqlalchemy import String, DateTime, ForeignKey, Table, Column, Integer, Boolean, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.models.base import Base

class RoomType(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    READONLY = "readonly"

room_members = Table(
    "room_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("room_id", Integer, ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime, server_default=func.now())
)

class RoomAdmin(Base):
    __tablename__ = "room_admins"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    promoted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    room: Mapped["Room"] = relationship("Room", foreign_keys=[room_id], back_populates="admins")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    promoted_by: Mapped["User | None"] = relationship("User", foreign_keys=[promoted_by_id])

class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    room_type: Mapped[RoomType] = mapped_column(SAEnum(RoomType), default=RoomType.PUBLIC, nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    members: Mapped[list["User"]] = relationship(
        "User", secondary=room_members, back_populates="rooms"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="room", cascade="all, delete-orphan"
    )
    admins: Mapped[list["RoomAdmin"]] = relationship(
        "RoomAdmin", back_populates="room", cascade="all, delete-orphan",
        foreign_keys="[RoomAdmin.room_id]"
    )
    warnings: Mapped[list["Warning"]] = relationship(
        "Warning", back_populates="room", cascade="all, delete-orphan"
    )
