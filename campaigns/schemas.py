from datetime import datetime
from pydantic import BaseModel

from campaigns.models import AttackType, CampaignStatus


class CampaignCreate(BaseModel):
    name: str
    description: str | None = None
    attack_type: AttackType
    target_group: str | None = None
    template_id: str | None = None
    scheduled_time: datetime | None = None


class CampaignOut(BaseModel):
    id: int
    name: str
    description: str | None
    attack_type: AttackType
    target_group: str | None
    template_id: str | None
    scheduled_time: datetime | None
    status: CampaignStatus
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TargetOut(BaseModel):
    id: int
    campaign_id: int
    email: str
    name: str | None
    department: str | None
    email_sent: bool
    email_opened: bool
    link_clicked: bool
    credential_attempt: bool
    file_download: bool
    reported: bool

    model_config = {"from_attributes": True}


class CampaignDetail(CampaignOut):
    targets: list[TargetOut] = []
