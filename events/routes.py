from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import require_analyst
from events.models import Event
from events.schemas import EventOut
from auth.models import User
from campaigns.models import Campaign
from database import get_db

router = APIRouter()


@router.get("/recent-events", response_model=list[EventOut],
            dependencies=[Depends(require_analyst)])
async def recent_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, le=200),
):
    """Return the N most recent events, enriched with user email and campaign name."""
    result = await db.execute(
        select(Event).order_by(desc(Event.timestamp)).limit(limit)
    )
    events = result.scalars().all()

    # Enrich with user/campaign names in bulk
    user_ids = {e.user_id for e in events if e.user_id}
    campaign_ids = {e.campaign_id for e in events if e.campaign_id}

    users: dict[int, str] = {}
    if user_ids:
        u_res = await db.execute(select(User.id, User.email).where(User.id.in_(user_ids)))
        users = {row.id: row.email for row in u_res}

    campaigns: dict[int, str] = {}
    if campaign_ids:
        c_res = await db.execute(select(Campaign.id, Campaign.name).where(Campaign.id.in_(campaign_ids)))
        campaigns = {row.id: row.name for row in c_res}

    out = []
    for e in events:
        o = EventOut.model_validate(e)
        o.user_email = users.get(e.user_id) if e.user_id else None
        o.campaign_name = campaigns.get(e.campaign_id) if e.campaign_id else None
        out.append(o)
    return out
