from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.models import RiskScore, RiskLevel
from auth.dependencies import require_admin, CurrentUser
from auth.models import User, UserRole
from campaigns.models import Campaign, CampaignTarget, CampaignStatus
from database import get_db

router = APIRouter()


class DashboardOverview(BaseModel):
    total_campaigns: int
    active_campaigns: int
    employees_tested: int
    avg_risk_score: float
    high_risk_users: int


@router.get("/dashboard", response_model=DashboardOverview,
            dependencies=[Depends(require_admin)])
async def dashboard(db: Annotated[AsyncSession, Depends(get_db)]):
    total_campaigns = (await db.execute(select(func.count()).select_from(Campaign))).scalar_one()
    active_campaigns = (await db.execute(
        select(func.count()).select_from(Campaign)
        .where(Campaign.status == CampaignStatus.running)
    )).scalar_one()
    employees_tested = (await db.execute(
        select(func.count(func.distinct(CampaignTarget.email))).select_from(CampaignTarget)
    )).scalar_one()

    avg_score_row = (await db.execute(select(func.avg(RiskScore.risk_score)))).scalar_one()
    avg_risk_score = round(float(avg_score_row or 0), 1)

    high_risk_users = (await db.execute(
        select(func.count()).select_from(RiskScore)
        .where(RiskScore.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]))
    )).scalar_one()

    return DashboardOverview(
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        employees_tested=employees_tested,
        avg_risk_score=avg_risk_score,
        high_risk_users=high_risk_users,
    )


class UserWithRisk(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    department: str | None
    risk_score: float | None = None
    risk_level: RiskLevel | None = None

    model_config = {"from_attributes": True}


@router.get("/users", response_model=list[UserWithRisk],
            dependencies=[Depends(require_admin)])
async def list_users(db: Annotated[AsyncSession, Depends(get_db)]):
    users = (await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    user_ids = [u.id for u in users]

    risk_rows = {}
    if user_ids:
        rs_q = await db.execute(select(RiskScore).where(RiskScore.user_id.in_(user_ids)))
        risk_rows = {rs.user_id: rs for rs in rs_q.scalars()}

    result = []
    for u in users:
        rs = risk_rows.get(u.id)
        result.append(UserWithRisk(
            id=u.id, name=u.name, email=u.email,
            role=u.role, department=u.department,
            risk_score=rs.risk_score if rs else None,
            risk_level=rs.risk_level if rs else None,
        ))
    return result


class RoleUpdate(BaseModel):
    role: UserRole


@router.put("/users/{user_id}/role", dependencies=[Depends(require_admin)])
async def update_user_role(
    user_id: int,
    body: RoleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = body.role
    db.add(user)
    return {"message": f"Role updated to {body.role.value}", "user_id": user_id}
