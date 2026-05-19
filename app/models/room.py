from sqlalchemy import String, DateTime, ForeignKey, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.models.base import Base

# Table d'association Many-to-Many entre les Utilisateurs et les Salons
room_members = Table(
    "room_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("room_id", Integer, ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime, server_default=func.now())
)

class Room(Base):
    """
    Modèle représentant un salon de discussion dans la base de données.
    """
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relations
    # Le créateur du salon
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id]
    )

    # Les membres actifs du salon (relation Many-to-Many)
    members: Mapped[list["User"]] = relationship(
        "User",
        secondary=room_members,
        back_populates="rooms"
    )

    # Les messages envoyés dans ce salon
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="room",
        cascade="all, delete-orphan"
    )
