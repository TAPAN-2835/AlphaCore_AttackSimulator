import enum
from datetime import datetime
from typing import Any

from sqlalchemy import String, Enum as SAEnum, DateTime, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class EventType(str, enum.Enum):
    EMAIL_SENT = "EMAIL_SENT"
    EMAIL_OPEN = "EMAIL_OPEN"
    LINK_CLICK = "LINK_CLICK"
    CREDENTIAL_ATTEMPT = "CREDENTIAL_ATTEMPT"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    EMAIL_REPORTED = "EMAIL_REPORTED"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"), nullable=True, index=True)
    event_type: Mapped[EventType] = mapped_column(SAEnum(EventType), nullable=False, index=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
