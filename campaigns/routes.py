from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.dependencies import CurrentUser, require_admin, require_analyst
from campaigns.models import Campaign, CampaignStatus
from campaigns.schemas import CampaignCreate, CampaignOut, CampaignDetail
from campaigns.service import (
    create_campaign,
    upload_targets_from_csv,
    start_campaign,
    complete_campaign,
)
from database import get_db

router = APIRouter()


@router.post("/create", response_model=CampaignOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
async def create(
    body: CampaignCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await create_campaign(db, body, current_user.id)


@router.get("/", response_model=list[CampaignOut],
            dependencies=[Depends(require_analyst)])
async def list_campaigns(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    return result.scalars().all()


@router.get("/{campaign_id}", response_model=CampaignDetail,
            dependencies=[Depends(require_analyst)])
async def get_campaign(campaign_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.id == campaign_id)
        .options(selectinload(Campaign.targets))
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("/{campaign_id}/start", response_model=CampaignOut,
             dependencies=[Depends(require_admin)])
async def launch_campaign(campaign_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status == CampaignStatus.running:
        raise HTTPException(status_code=400, detail="Campaign is already running")
    return await start_campaign(db, campaign)


@router.post("/{campaign_id}/complete", response_model=CampaignOut,
             dependencies=[Depends(require_admin)])
async def finish_campaign(campaign_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await complete_campaign(db, campaign)


@router.post("/upload-users", dependencies=[Depends(require_admin)])
async def upload_users(
    campaign_id: int,
    file: Annotated[UploadFile, File(...)],
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Upload a CSV of target users (email, name, department)."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    content = await file.read()
    targets = await upload_targets_from_csv(
        db, campaign_id, content.decode("utf-8"), background_tasks
    )
    return {"message": f"{len(targets)} targets uploaded", "campaign_id": campaign_id}


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
async def delete_campaign(campaign_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await db.delete(campaign)
