"""
Advanced hybrid risk assignment logic.
Combines machine learning anomaly scores with behavioral heuristics.
Pure Python module — no FastAPI imports.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def assign_risk_levels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes a hybrid risk score and assigns categorical risk levels.
    
    Weights:
    - 50% Anomaly Score (from Model)
    - 20% Failure Ratio (if success_ratio exists)
    - 15% Activity Spike (z-score of request_rate_per_minute)
    - 15% After-Hours Activity (if window_start exists)
    """
    if df.empty:
        return df

    result = df.copy()

    # 1. Initialize component scores (0-100 scale)
    n_rows = len(result)
    
    # Anomaly Component (50%)
    # If model hasn't run, default to 0
    anomaly_base = result.get("risk_score", pd.Series([0.0] * n_rows))
    
    # Failure Component (20%)
    if "success_ratio" in result.columns:
        failure_component = (1.0 - result["success_ratio"]) * 100.0
    else:
        failure_component = pd.Series([0.0] * n_rows)
        
    # Activity Spike Component (15%)
    if "request_rate_per_minute" in result.columns and n_rows > 1:
        try:
            scaler = StandardScaler()
            spike_z = scaler.fit_transform(result[["request_rate_per_minute"]])
            # Normalize absolute Z-score to 0-100 (cap at Z=3.0 for max risk)
            spike_component = np.clip(np.abs(spike_z.flatten()) / 3.0 * 100.0, 0, 100)
        except Exception:
            spike_component = np.zeros(n_rows)
    else:
        spike_component = np.zeros(n_rows)
        
    # After-Hours Component (15%)
    if "window_start" in result.columns:
        try:
            # Ensure datetime
            times = pd.to_datetime(result["window_start"])
            hours = times.dt.hour
            # Higher risk for 22:00 - 06:00
            # 22, 23, 0, 1, 2, 3, 4, 5
            after_hours_mask = (hours >= 22) | (hours <= 5)
            after_hours_component = np.where(after_hours_mask, 100.0, 0.0)
        except Exception:
            after_hours_component = np.zeros(n_rows)
    else:
        after_hours_component = np.zeros(n_rows)

    # 2. Calculate Final Hybrid Risk Score
    # Handle NaNs in components
    anomaly_base = anomaly_base.fillna(0)
    failure_component = failure_component.fillna(0)
    spike_component = np.nan_to_num(spike_component)
    after_hours_component = np.nan_to_num(after_hours_component)

    hybrid_score = (
        (0.50 * anomaly_base) +
        (0.20 * failure_component) +
        (0.15 * spike_component) +
        (0.15 * after_hours_component)
    )
    
    # Normalize final score to 0-100
    if hybrid_score.max() > hybrid_score.min():
        result["risk_score"] = 100.0 * (hybrid_score - hybrid_score.min()) / (hybrid_score.max() - hybrid_score.min())
    else:
        # If all scores are the same, use the raw hybrid score capped at 100
        result["risk_score"] = np.clip(hybrid_score, 0, 100)

    # 3. Categorical Risk Levels
    def _to_risk_level(score: float) -> str:
        if score >= 75:
            return "HIGH"
        if score >= 40:
            return "MEDIUM"
        return "LOW"

    result["risk_level"] = result["risk_score"].apply(_to_risk_level)

    # 4. Sort and return
    result = result.sort_values("risk_score", ascending=False).reset_index(drop=True)
    
    return result
