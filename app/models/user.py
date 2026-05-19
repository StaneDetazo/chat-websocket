from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.models.base import Base

class User(Base):
    """
    Modèle représentant un utilisateur dans la base de données.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relations
    # Relation Many-to-Many avec les salons (Rooms) via la table d'association room_members
    rooms: Mapped[list["Room"]] = relationship(
        "Room",
        secondary="room_members",
        back_populates="members"
    )

    # Messages envoyés par l'utilisateur (salons ou privés)
    sent_messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="[Message.sender_id]"
    )

    # Messages privés reçus par l'utilisateur
    received_private_messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="receiver",
        foreign_keys="[Message.receiver_id]"
    )
