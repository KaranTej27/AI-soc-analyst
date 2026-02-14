"""
Anomaly detection using Isolation Forest.
Pure data processing module — no FastAPI or route logic.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# Feature columns required for anomaly detection
REQUIRED_FEATURES = [
    "total_requests",
    "failed_requests",
    "success_ratio",
    "unique_endpoints",
    "request_rate_per_minute",
    "avg_time_gap_seconds",
]


def run_isolation_forest(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run Isolation Forest anomaly detection on behavioral features.
    Returns a copy of the input with anomaly_label, anomaly_score, and risk_score.
    """
    # -------------------------------------------------------------------------
    # STEP 1 — Validate Input
    # -------------------------------------------------------------------------
    if df.empty:
        raise ValueError("Anomaly detection failed: Input dataset is empty.")

    actual_cols = set(df.columns)
    missing = set(REQUIRED_FEATURES) - actual_cols
    if missing:
        raise ValueError(
            f"Anomaly detection failed: Missing required feature columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    # Work on a copy — do not modify input in-place
    result = df.copy()

    # -------------------------------------------------------------------------
    # STEP 2 — Select Feature Matrix
    # -------------------------------------------------------------------------
    X = df[REQUIRED_FEATURES].copy()
    valid_mask = ~X.isna().any(axis=1)
    valid_indices = result.index[valid_mask]

    if valid_indices.empty:
        raise ValueError("Anomaly detection failed: No valid numerical data available after filtering missing values.")

    X_clean = X.loc[valid_indices].astype(float)
    X_clean = X_clean.dropna()

    if X_clean.empty:
        raise ValueError("Anomaly detection failed: Feature matrix became empty after cleaning.")

    # Recompute valid_indices after dropna
    valid_indices = X_clean.index

    # -------------------------------------------------------------------------
    # STEP 3 — Scale Features
    # -------------------------------------------------------------------------
    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_clean)
    except Exception as e:
        raise ValueError(f"Normalization failed: {str(e)}")

    # -------------------------------------------------------------------------
    # STEP 4 — Train Isolation Forest
    # -------------------------------------------------------------------------
    try:
        # Minimum rows needed to build a reasonable model
        if len(X_scaled) < 2:
            # For 1 row, we can't really do anomaly detection effectively with contamination
            # Just mark it as normal
            result["anomaly_label"] = np.nan
            result["anomaly_score"] = np.nan
            result["risk_score"] = np.nan
            result.loc[valid_indices, "anomaly_label"] = 1
            result.loc[valid_indices, "anomaly_score"] = 0.0
            result.loc[valid_indices, "risk_score"] = 50.0
            return result

        model = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100,
        )
        model.fit(X_scaled)
    except Exception as e:
        raise ValueError(f"Model training failed: {str(e)}")

    # -------------------------------------------------------------------------
    # STEP 5 — Compute Outputs
    # -------------------------------------------------------------------------
    try:
        # 1 = normal, -1 = anomaly
        anomaly_label = model.predict(X_scaled)
        anomaly_score = model.decision_function(X_scaled)
    except Exception as e:
        raise ValueError(f"Prediction failed: {str(e)}")

    # -------------------------------------------------------------------------
    # STEP 6 — Normalize Anomaly Score to 0–100 Risk Scale
    # -------------------------------------------------------------------------
    raw_min = anomaly_score.min()
    raw_max = anomaly_score.max()
    if raw_max > raw_min:
        risk_score = 100.0 * (raw_max - anomaly_score) / (raw_max - raw_min)
    else:
        risk_score = np.full_like(anomaly_score, 50.0)

    # -------------------------------------------------------------------------
    # STEP 7 — Return Updated DataFrame
    # -------------------------------------------------------------------------
    result["anomaly_label"] = np.nan
    result["anomaly_score"] = np.nan
    result["risk_score"] = np.nan

    result.loc[valid_indices, "anomaly_label"] = anomaly_label
    result.loc[valid_indices, "anomaly_score"] = anomaly_score
    result.loc[valid_indices, "risk_score"] = risk_score

    return result
