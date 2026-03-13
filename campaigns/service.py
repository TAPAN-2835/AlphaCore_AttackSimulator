import csv
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from campaigns.models import Campaign, CampaignTarget, CampaignStatus, SimulationToken
from campaigns.schemas import CampaignCreate
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def create_campaign(
    db: AsyncSession,
    data: CampaignCreate,
    created_by: int,
) -> Campaign:
    campaign = Campaign(
        name=data.name,
        description=data.description,
        attack_type=data.attack_type,
        target_group=data.target_group,
        template_id=data.template_id,
        scheduled_time=data.scheduled_time,
        created_by=created_by,
        status=CampaignStatus.scheduled if data.scheduled_time else CampaignStatus.draft,
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return campaign


async def upload_targets_from_csv(
    db: AsyncSession,
    campaign_id: int,
    csv_content: str,
    background_tasks: BackgroundTasks,
) -> list[CampaignTarget]:
    reader = csv.DictReader(io.StringIO(csv_content))
    targets: list[CampaignTarget] = []
    tokens: list[SimulationToken] = []
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.TOKEN_EXPIRY_HOURS)

    for row in reader:
        email = row.get("email", "").strip()
        if not email:
            continue
        target = CampaignTarget(
            campaign_id=campaign_id,
            email=email,
            name=row.get("name", "").strip() or None,
            department=row.get("department", "").strip() or None,
        )
        db.add(target)
        targets.append(target)

        token = SimulationToken(
            token=uuid.uuid4().hex,
            campaign_id=campaign_id,
            target_email=email,
            expires_at=expires_at,
        )
        db.add(token)
        tokens.append(token)

    await db.flush()
    # Schedule email dispatch in background (mocked)
    background_tasks.add_task(_send_phishing_emails_mock, targets, tokens)
    return targets


async def start_campaign(db: AsyncSession, campaign: Campaign) -> Campaign:
    campaign.status = CampaignStatus.running
    db.add(campaign)
    await db.flush()
    return campaign


async def complete_campaign(db: AsyncSession, campaign: Campaign) -> Campaign:
    campaign.status = CampaignStatus.completed
    db.add(campaign)
    await db.flush()
    return campaign


# ── Private helpers ───────────────────────────────────────────────────────────

def _send_phishing_emails_mock(
    targets: list[CampaignTarget],
    tokens: list[SimulationToken],
) -> None:
    """
    In production: integrate with SendGrid / SES / SMTP.
    Here we simply log the simulated send for hackathon purposes.
    """
    for target, token in zip(targets, tokens):
        sim_link = f"{settings.SIM_BASE_URL}/sim/{token.token}"
        logger.info(
            "[MOCK EMAIL] To: %s | Link: %s",
            target.email,
            sim_link,
        )
