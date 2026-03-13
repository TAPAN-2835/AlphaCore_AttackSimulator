from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from campaigns.models import SimulationToken, CampaignTarget, Campaign
from config import get_settings
from database import get_db
from events.logger import log_event
from events.models import EventType
from simulation.credential_pages import (
    microsoft_login_page,
    corporate_login_page,
    awareness_page,
)
from simulation.malware_simulation import generate_dummy_file

settings = get_settings()
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_valid_token(token: str, db: AsyncSession) -> SimulationToken:
    result = await db.execute(
        select(SimulationToken).where(SimulationToken.token == token)
    )
    sim_token = result.scalar_one_or_none()
    if not sim_token:
        raise HTTPException(status_code=404, detail="Invalid simulation token")
    if sim_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Simulation token has expired")
    return sim_token


async def _mark_target_flag(db: AsyncSession, campaign_id: int, email: str, field: str):
    result = await db.execute(
        select(CampaignTarget).where(
            CampaignTarget.campaign_id == campaign_id,
            CampaignTarget.email == email,
        )
    )
    target = result.scalar_one_or_none()
    if target:
        setattr(target, field, True)
        db.add(target)


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/{token}", response_class=HTMLResponse)
async def track_link_click(
    token: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Entry point for phishing links. Logs LINK_CLICK, then serves a fake login page.
    Token is NOT marked as used yet — the credential-submit endpoint does that.
    """
    sim_token = await _get_valid_token(token, db)

    # Log the click
    await log_event(
        db=db,
        event_type=EventType.LINK_CLICK,
        request=request,
        user_id=sim_token.user_id,
        campaign_id=sim_token.campaign_id,
        metadata={"email": sim_token.target_email},
    )
    await _mark_target_flag(db, sim_token.campaign_id, sim_token.target_email, "link_clicked")

    action_url = f"{settings.SIM_BASE_URL}/sim/credential"

    # Use campaign attack_type to pick the right template
    c_result = await db.execute(select(Campaign).where(Campaign.id == sim_token.campaign_id))
    campaign = c_result.scalar_one_or_none()

    if campaign and campaign.attack_type.value == "malware_download":
        # Redirect to download endpoint directly
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{settings.SIM_BASE_URL}/sim/download/{token}")

    # Pick page template (alternating by token hash for variety)
    if int(token[:4], 16) % 2 == 0:
        html = microsoft_login_page(token, action_url)
    else:
        html = corporate_login_page(token, action_url)

    return HTMLResponse(content=html)


class CredentialSubmit(BaseModel):
    token: str
    username: str
    password: str  # NEVER stored — only existence of attempt is logged


@router.post("/credential")
async def credential_submit(
    body: CredentialSubmit,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Receives fake credential form submission.
    NEVER stores the password — only logs that an attempt occurred.
    """
    sim_token = await _get_valid_token(body.token, db)

    # Mark token as used
    sim_token.used = True
    db.add(sim_token)

    # Log — password is intentionally excluded from metadata
    await log_event(
        db=db,
        event_type=EventType.CREDENTIAL_ATTEMPT,
        request=request,
        user_id=sim_token.user_id,
        campaign_id=sim_token.campaign_id,
        metadata={"username_provided": body.username, "password_stored": False},
    )
    await _mark_target_flag(db, sim_token.campaign_id, sim_token.target_email, "credential_attempt")

    # Trigger async risk score update
    from analytics.risk_engine import compute_and_save_risk
    if sim_token.user_id:
        await compute_and_save_risk(db, sim_token.user_id)

    return "This was a security awareness simulation. Never enter credentials on suspicious websites."


@router.get("/download/{token}")
async def malware_download(
    token: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Simulates a malware download. Returns a harmless ZIP with a drill notice.
    """
    sim_token = await _get_valid_token(token, db)
    sim_token.used = True
    db.add(sim_token)

    await log_event(
        db=db,
        event_type=EventType.FILE_DOWNLOAD,
        request=request,
        user_id=sim_token.user_id,
        campaign_id=sim_token.campaign_id,
        metadata={"email": sim_token.target_email},
    )
    await _mark_target_flag(db, sim_token.campaign_id, sim_token.target_email, "file_download")

    if sim_token.user_id:
        from analytics.risk_engine import compute_and_save_risk
        await compute_and_save_risk(db, sim_token.user_id)

    file_bytes, filename = generate_dummy_file()
    
    # MIME types handling
    media_type = "application/octet-stream"
    if filename.endswith(".zip"):
        media_type = "application/zip"
    elif filename.endswith(".docm"):
        media_type = "application/vnd.ms-word.document.macroEnabled.12"
    elif filename.endswith(".exe"):
        media_type = "application/x-msdownload"

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/report/{token}", status_code=status.HTTP_200_OK)
async def email_reported(
    token: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Endpoint for a 'Report Phishing' button in an email template.
    Logs EMAIL_REPORTED event.
    """
    sim_token = await _get_valid_token(token, db)

    await log_event(
        db=db,
        event_type=EventType.EMAIL_REPORTED,
        request=request,
        user_id=sim_token.user_id,
        campaign_id=sim_token.campaign_id,
        metadata={"email": sim_token.target_email},
    )
    await _mark_target_flag(db, sim_token.campaign_id, sim_token.target_email, "reported")

    if sim_token.user_id:
        from analytics.risk_engine import compute_and_save_risk
    return {"message": "Email reported successfully."}


@router.get("/track/{token}")
async def track_email_open(
    token: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    1x1 transparent tracking pixel. Logs EMAIL_OPEN event.
    """
    try:
        sim_token = await _get_valid_token(token, db)
    except HTTPException:
        # Silently fail for pixel loads to not break email client renders
        return Response(content=b"", media_type="image/gif")

    await log_event(
        db=db,
        event_type=EventType.EMAIL_OPEN,
        request=request,
        user_id=sim_token.user_id,
        campaign_id=sim_token.campaign_id,
        metadata={"email": sim_token.target_email},
    )
    await _mark_target_flag(db, sim_token.campaign_id, sim_token.target_email, "email_opened")

    # 1x1 transparent GIF
    pixel_data = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00"
        b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )

    return Response(content=pixel_data, media_type="image/gif")
