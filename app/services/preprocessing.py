"""
Behavioral feature engineering for log anomaly detection.
Pure data processing module — no FastAPI or route logic.
"""

import pandas as pd
import numpy as np


def build_features(file_path: str) -> pd.DataFrame:
    """
    Load log CSV, validate schema, create 5-min time windows per IP,
    and engineer behavioral features for anomaly detection.
    """
    # -------------------------------------------------------------------------
    # STEP 1 — Load CSV
    # -------------------------------------------------------------------------
    df = pd.read_csv(file_path)

    # -------------------------------------------------------------------------
    # STEP 2 — Validate Required Columns
    # -------------------------------------------------------------------------
    required = {"ip", "timestamp", "status", "endpoint"}
    actual_cols = set(df.columns)
    missing = required - actual_cols
    if missing:
        raise ValueError(
            f"Dataset missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    # Parse timestamp as datetime and sort by it
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # -------------------------------------------------------------------------
    # STEP 3 — Create 5-Minute Time Windows
    # Group by: ip + 5-minute window
    # -------------------------------------------------------------------------
    grouped = df.groupby(
        ["ip", pd.Grouper(key="timestamp", freq="5min")],
        dropna=False,
    )

    # -------------------------------------------------------------------------
    # STEP 4 — Engineer Features For Each Group
    # -------------------------------------------------------------------------

    def _avg_time_gap_seconds(g: pd.DataFrame) -> float:
        """Mean seconds between consecutive requests within the group."""
        if len(g) < 2:
            return np.nan
        g = g.sort_values("timestamp")
        diffs = g["timestamp"].diff().dt.total_seconds()
        return float(diffs.dropna().mean())

    features = grouped.agg(
        total_requests=("status", "size"),
        failed_requests=("status", lambda s: (s >= 400).sum()),
        unique_endpoints=("endpoint", "nunique"),
    ).reset_index()

    features = features.rename(columns={"timestamp": "window_start"})

    # Compute derived features
    features["success_ratio"] = features.apply(
        lambda r: 1 - r["failed_requests"] / r["total_requests"]
        if r["total_requests"] > 0
        else np.nan,
        axis=1,
    )
    features["request_rate_per_minute"] = features["total_requests"] / 5.0

    # avg_time_gap_seconds requires per-group timestamp diffs — compute via grouped apply
    gap_series = grouped.apply(_avg_time_gap_seconds).reset_index(drop=True)
    features["avg_time_gap_seconds"] = gap_series.values

    # -------------------------------------------------------------------------
    # STEP 5 — Return Clean Feature DataFrame
    # -------------------------------------------------------------------------
    result = features[
        [
            "ip",
            "window_start",
            "total_requests",
            "failed_requests",
            "success_ratio",
            "unique_endpoints",
            "request_rate_per_minute",
            "avg_time_gap_seconds",
        ]
    ].copy()

    result = result.dropna(how="all", subset=result.columns[2:])
    result = result.reset_index(drop=True)

    # Ensure correct numeric types
    result["total_requests"] = result["total_requests"].astype(int)
    result["failed_requests"] = result["failed_requests"].astype(int)
    result["unique_endpoints"] = result["unique_endpoints"].astype(int)
    result["success_ratio"] = result["success_ratio"].astype(float)
    result["request_rate_per_minute"] = result["request_rate_per_minute"].astype(
        float
    )
    result["avg_time_gap_seconds"] = result["avg_time_gap_seconds"].astype(float)

    return result
