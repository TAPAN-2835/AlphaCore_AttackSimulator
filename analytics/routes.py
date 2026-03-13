from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.models import RiskScore, RiskLevel
from analytics.risk_engine import compute_and_save_risk, get_event_counts_for_user
from auth.dependencies import require_analyst, CurrentUser
from auth.models import User
from campaigns.models import CampaignTarget, Campaign
from events.models import Event, EventType
from database import get_db

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class DeptRate(BaseModel):
    name: str
    rate: float
    score: float | None = None


class OverviewResponse(BaseModel):
    click_rate: float
    credential_rate: float
    report_rate: float
    high_risk_departments: list[DeptRate]


class UserRiskResponse(BaseModel):
    user_id: int
    email: str
    risk_score: float
    risk_level: RiskLevel
    events: dict


class TrendPoint(BaseModel):
    campaign: str
    total_events: int
    clicks: int
    credentials: int
    downloads: int


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/overview", response_model=OverviewResponse,
            dependencies=[Depends(require_analyst)])
async def analytics_overview(db: Annotated[AsyncSession, Depends(get_db)]):
    total_targets = (await db.execute(select(func.count()).select_from(CampaignTarget))).scalar_one() or 1

    clicks = (await db.execute(
        select(func.count()).select_from(CampaignTarget).where(CampaignTarget.link_clicked == True)
    )).scalar_one()
    creds = (await db.execute(
        select(func.count()).select_from(CampaignTarget).where(CampaignTarget.credential_attempt == True)
    )).scalar_one()
    reported = (await db.execute(
        select(func.count()).select_from(CampaignTarget).where(CampaignTarget.reported == True)
    )).scalar_one()

    # High-risk departments: aggregate avg risk_score by user.department
    dept_rows = await db.execute(
        select(User.department, func.avg(RiskScore.risk_score).label("avg_score"))
        .join(RiskScore, User.id == RiskScore.user_id)
        .where(User.department.isnot(None))
        .group_by(User.department)
        .order_by(func.avg(RiskScore.risk_score).desc())
        .limit(5)
    )
    high_risk_depts = [
        DeptRate(name=row.department, rate=round(row.avg_score, 1), score=round(row.avg_score, 1))
        for row in dept_rows
    ]

    return OverviewResponse(
        click_rate=round(clicks / total_targets * 100, 1),
        credential_rate=round(creds / total_targets * 100, 1),
        report_rate=round(reported / total_targets * 100, 1),
        high_risk_departments=high_risk_depts,
    )


@router.get("/user/{user_id}", response_model=UserRiskResponse,
            dependencies=[Depends(require_analyst)])
async def user_risk(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rs = await compute_and_save_risk(db, user_id)
    counts = await get_event_counts_for_user(db, user_id)

    return UserRiskResponse(
        user_id=user_id,
        email=user.email,
        risk_score=rs.risk_score,
        risk_level=rs.risk_level,
        events=counts,
    )


@router.get("/click-rate", response_model=list[DeptRate],
            dependencies=[Depends(require_analyst)])
async def click_rate_by_dept(db: Annotated[AsyncSession, Depends(get_db)]):
    rows = await db.execute(
        select(
            CampaignTarget.department,
            func.count().label("total"),
            func.sum(CampaignTarget.link_clicked.cast(type_=None)).label("clicked"),
        )
        .where(CampaignTarget.department.isnot(None))
        .group_by(CampaignTarget.department)
    )
    result = []
    for row in rows:
        total = row.total or 1
        clicked = int(row.clicked or 0)
        result.append(DeptRate(name=row.department, rate=round(clicked / total * 100, 1)))
    return sorted(result, key=lambda x: x.rate, reverse=True)


@router.get("/credential-rate", response_model=list[DeptRate],
            dependencies=[Depends(require_analyst)])
async def credential_rate_by_dept(db: Annotated[AsyncSession, Depends(get_db)]):
    rows = await db.execute(
        select(
            CampaignTarget.department,
            func.count().label("total"),
            func.sum(CampaignTarget.credential_attempt.cast(type_=None)).label("attempted"),
        )
        .where(CampaignTarget.department.isnot(None))
        .group_by(CampaignTarget.department)
    )
    result = []
    for row in rows:
        total = row.total or 1
        attempted = int(row.attempted or 0)
        result.append(DeptRate(name=row.department, rate=round(attempted / total * 100, 1)))
    return sorted(result, key=lambda x: x.rate, reverse=True)


@router.get("/campaign-trend", response_model=list[TrendPoint],
            dependencies=[Depends(require_analyst)])
async def campaign_trend(db: Annotated[AsyncSession, Depends(get_db)]):
    campaigns = (await db.execute(select(Campaign).order_by(Campaign.created_at))).scalars().all()
    result = []
    for c in campaigns:
        totals = await db.execute(
            select(func.count()).where(Event.campaign_id == c.id)
        )
        clicks = (await db.execute(
            select(func.count()).where(Event.campaign_id == c.id, Event.event_type == EventType.LINK_CLICK)
        )).scalar_one()
        creds = (await db.execute(
            select(func.count()).where(Event.campaign_id == c.id, Event.event_type == EventType.CREDENTIAL_ATTEMPT)
        )).scalar_one()
        downloads = (await db.execute(
            select(func.count()).where(Event.campaign_id == c.id, Event.event_type == EventType.FILE_DOWNLOAD)
        )).scalar_one()
        result.append(TrendPoint(
            campaign=c.name,
            total_events=totals.scalar_one(),
            clicks=clicks,
            credentials=creds,
            downloads=downloads,
        ))
    return result
