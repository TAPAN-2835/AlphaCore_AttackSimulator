def calculate_risk(click_rate, credential_rate, report_rate):

    risk_score = (
        (click_rate * 0.4) +
        (credential_rate * 0.5) -
        (report_rate * 0.3)
    )

    return round(risk_score, 3)