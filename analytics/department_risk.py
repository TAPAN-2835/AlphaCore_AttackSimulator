import pandas as pd
from .risk_score import calculate_risk

def department_risk(events_df):

    dept_stats = events_df.groupby("department").agg({
        "clicked": "mean",
        "credential_entered": "mean",
        "reported": "mean"
    }).reset_index()

    dept_stats["risk_score"] = dept_stats.apply(
        lambda row: calculate_risk(
            row["clicked"],
            row["credential_entered"],
            row["reported"]
        ),
        axis=1
    )

    return dept_stats.sort_values("risk_score", ascending=False)