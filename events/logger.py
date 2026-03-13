import logging
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from events.models import Event, EventType

logger = logging.getLogger(__name__)


async def log_event(
    db: AsyncSession,
    event_type: EventType,
    request: Request | None = None,
    user_id: int | None = None,
    campaign_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> Event:
    """
    Central event logger. Called from simulation, admin, and analytics modules.
    Never stores passwords — callers must strip sensitive data from metadata.
    """
    ip = None
    if request:
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else None

    event = Event(
        user_id=user_id,
        campaign_id=campaign_id,
        event_type=event_type,
        metadata_=metadata,
        ip_address=ip,
    )
    db.add(event)
    await db.flush()
    logger.info("[EVENT] %s | user=%s | campaign=%s | ip=%s", event_type, user_id, campaign_id, ip)
    return event
