from fastapi import APIRouter
from .service import compute_overall_risk

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/risk-summary")
def risk_summary():

    # later you will fetch events from DB
    dummy = {
        "click_rate": 0.35,
        "credential_rate": 0.18,
        "report_rate": 0.22,
        "risk_score": 0.31
    }

    return dummy