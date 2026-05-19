from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.models.base import Base

class Message(Base):
    """
    Modèle représentant un message (public ou privé) dans la base de données.
    """
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Identifiant du salon (si c'est un message public dans un salon)
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True)
    
    # Identifiant du destinataire (si c'est un message privé)
    receiver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Indicateur pour savoir s'il s'agit d'un message privé
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relations
    # Expéditeur du message
    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_messages"
    )

    # Salon associé (facultatif si message privé)
    room: Mapped["Room"] = relationship(
        "Room",
        foreign_keys=[room_id],
        back_populates="messages"
    )

    # Destinataire du message (facultatif si message de salon)
    receiver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_private_messages"
    )
