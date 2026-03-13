from .department_risk import department_risk
from .risk_score import calculate_risk

def compute_overall_risk(df):

    click_rate = df["clicked"].mean()
    credential_rate = df["credential_entered"].mean()
    report_rate = df["reported"].mean()

    risk_score = calculate_risk(
        click_rate,
        credential_rate,
        report_rate
    )

    return {
        "click_rate": click_rate,
        "credential_rate": credential_rate,
        "report_rate": report_rate,
        "risk_score": risk_score
    }


def compute_department_risk(df):
    return department_risk(df)