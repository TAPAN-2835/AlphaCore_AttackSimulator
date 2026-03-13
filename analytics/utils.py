def classify_risk(score):

    if score > 0.6:
        return "HIGH"

    if score > 0.3:
        return "MEDIUM"

    return "LOW"