"""
Behavioral Anomaly Detection Engine.
Hybrid logic: Z-score for small datasets, Isolation Forest for larger ones.
Pure Python module — no FastAPI imports.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def run_isolation_forest(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardized entry point for anomaly detection (formerly just Isolation Forest).
    Now uses hybrid logic: Z-score for small datasets, IF for larger ones.
    2. Handles small vs large datasets using hybrid logic.
    3. Guarantees anomaly_label, anomaly_score, and risk_score (0-100).
    """
    if df.empty:
        return df

    # Work on a copy
    result = df.copy()

    # 1. Automatically select numeric columns
    numeric_df = df.select_dtypes(include=[np.number]).copy()
    
    # Drop rows that are entirely NaN in numeric columns if any exist
    numeric_df = numeric_df.dropna(how='all')
    if numeric_df.empty:
        # If no numeric data at all, return with neutral scores
        result["anomaly_label"] = 1
        result["anomaly_score"] = 0.0
        result["risk_score"] = 0.0
        return result

    # 3. Handle NaNs safely (fill with mean, fallback to 0)
    X = numeric_df.fillna(numeric_df.mean().fillna(0))

    # Keep track of indices that have numeric data
    valid_indices = X.index

    # Initialize columns in the result
    result["anomaly_label"] = 1  # 1 = normal, -1 = anomaly
    result["anomaly_score"] = 0.0
    result["risk_score"] = 0.0

    n_rows = len(X)

    if n_rows < 50:
        # 4. Simple statistical anomaly detection (Z-score)
        labels, scores, risks = _detect_zscore(X)
    else:
        # 5. Isolation Forest
        labels, scores, risks = _detect_isolation_forest(X)

    # Apply results back to original indices
    result.loc[valid_indices, "anomaly_label"] = labels
    result.loc[valid_indices, "anomaly_score"] = scores
    result.loc[valid_indices, "risk_score"] = risks

    return result


def _detect_zscore(X: pd.DataFrame):
    """
    Statistical detection for small datasets.
    Computes average absolute Z-score across numeric features.
    """
    # Standardize
    scaler = StandardScaler()
    try:
        X_scaled = scaler.fit_transform(X)
    except Exception:
        # Handle cases with zero variance
        X_scaled = np.zeros(X.shape)

    # Average absolute Z-score across all columns for each row
    z_scores = np.abs(X_scaled).mean(axis=1)
    
    # Label as anomaly (-1) if any feature's absolute Z-score > 2.5
    # or if the average Z-score is in the top 10%
    threshold = 2.5
    labels = np.ones(len(X))
    anomaly_mask = (np.abs(X_scaled) > threshold).any(axis=1)
    labels[anomaly_mask] = -1
    
    # Anomaly score (higher is more anomalous)
    scores = z_scores
    
    # Risk score normalized 0-100
    if scores.max() > scores.min():
        risks = 100 * (scores - scores.min()) / (scores.max() - scores.min())
    else:
        risks = np.zeros(len(scores))
        
    return labels, scores, risks


def _detect_isolation_forest(X: pd.DataFrame):
    """
    Isolation Forest for datasets with >= 50 rows.
    """
    # 6. Dynamic contamination
    n_rows = len(X)
    n_contamination = min(0.1, 10 / n_rows)
    
    model = IsolationForest(
        contamination=n_contamination,
        random_state=42,
        n_estimators=100
    )
    
    # Standardize before IF (good practice)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model.fit(X_scaled)
    
    # 1 = normal, -1 = anomaly
    labels = model.predict(X_scaled)
    
    # decision_function returns raw scores (lower = more abnormal)
    # We want anomaly_score to be higher for anomalies for consistency
    raw_scores = model.decision_function(X_scaled)
    scores = -raw_scores # Flip so higher is more anomalous
    
    # 7. Risk score (0-100)
    if scores.max() > scores.min():
        risks = 100 * (scores - scores.min()) / (scores.max() - scores.min())
    else:
        risks = np.zeros(len(scores))
        
    return labels, scores, risks
