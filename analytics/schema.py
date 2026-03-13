from pydantic import BaseModel


class RiskSummary(BaseModel):

    click_rate: float
    credential_rate: float
    report_rate: float
    risk_score: float