"""
Translate numerical risk scores into categorical risk levels for dashboard display.
Pure data processing module — no FastAPI or route logic.
"""

import numpy as np
import pandas as pd


def assign_risk_levels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map risk_score to categorical risk_level (HIGH / MEDIUM / LOW).
    Returns a copy sorted by risk_score descending.
    """
    # -------------------------------------------------------------------------
    # STEP 1 — Validate Input
    # -------------------------------------------------------------------------
    if "risk_score" not in df.columns:
        raise ValueError(
            f"Risk assignment failed: Column 'risk_score' not found in data. "
            f"Current columns: {list(df.columns)}"
        )

    # -------------------------------------------------------------------------
    # STEP 2 — Work on a Copy
    # -------------------------------------------------------------------------
    result = df.copy()

    # -------------------------------------------------------------------------
    # STEP 3 & 4 — Define Risk Thresholds and Add risk_level Column
    # -------------------------------------------------------------------------
    # risk_score >= 75 → "HIGH"
    # risk_score >= 40 → "MEDIUM"
    # risk_score < 40  → "LOW"
    # NaN → NaN
    def _to_risk_level(score: float) -> str:
        if pd.isna(score):
            return np.nan
        if score >= 75:
            return "HIGH"
        if score >= 40:
            return "MEDIUM"
        return "LOW"

    result["risk_level"] = result["risk_score"].apply(_to_risk_level)

    # -------------------------------------------------------------------------
    # STEP 5 — Sort Output (highest risk at top)
    # -------------------------------------------------------------------------
    result = result.sort_values("risk_score", ascending=False).reset_index(
        drop=True
    )

    # -------------------------------------------------------------------------
    # STEP 6 — Return Updated DataFrame
    # -------------------------------------------------------------------------
    return result
