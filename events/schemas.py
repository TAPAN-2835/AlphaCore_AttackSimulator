from datetime import datetime
from pydantic import BaseModel

from events.models import EventType


class EventOut(BaseModel):
    id: int
    user_id: int | None
    campaign_id: int | None
    event_type: EventType
    ip_address: str | None
    timestamp: datetime
    # Enriched fields joined in the route
    user_email: str | None = None
    campaign_name: str | None = None

    model_config = {"from_attributes": True}
