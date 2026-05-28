from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    rooms: Mapped[list["Room"]] = relationship(
        "Room", secondary="room_members", back_populates="members"
    )

    sent_messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="sender", foreign_keys="[Message.sender_id]"
    )

    received_private_messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="receiver", foreign_keys="[Message.receiver_id]"
    )

    warnings: Mapped[list["Warning"]] = relationship(
        "Warning", back_populates="user", foreign_keys="[Warning.user_id]"
    )

    given_warnings: Mapped[list["Warning"]] = relationship(
        "Warning", back_populates="given_by", foreign_keys="[Warning.given_by_id]"
    )
