from datetime import datetime
from pydantic import BaseModel, EmailStr

from auth.models import UserRole
from campaigns.models import AttackType, CampaignStatus
from events.models import EventType


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.employee
    department: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    department: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


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
