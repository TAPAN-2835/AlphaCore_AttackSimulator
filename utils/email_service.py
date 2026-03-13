import logging
from config import get_settings
from campaigns.models import CampaignTarget, SimulationToken

settings = get_settings()
logger = logging.getLogger(__name__)

def send_phishing_emails_mock(
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