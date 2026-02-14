"""
Behavioral feature engineering for log anomaly detection.
Pure data processing module — no FastAPI or route logic.
"""

import pandas as pd
import numpy as np
from app.services.schema_adapter import detect_and_standardize_schema


def build_features(file_path: str) -> pd.DataFrame:
    """
    Load log CSV, validate schema, create 5-min time windows per IP,
    and engineer behavioral features for anomaly detection.
    """
    # -------------------------------------------------------------------------
    # STEP 1 — Load CSV & Normalize Schema
    # -------------------------------------------------------------------------
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")

    if df.empty:
        raise ValueError("The uploaded CSV file is empty.")

    # Standardize Schema: Normalize headers, variants, and defaults
    df = detect_and_standardize_schema(df)

    # -------------------------------------------------------------------------
    # STEP 2 — Validate & Clean Data
    # -------------------------------------------------------------------------
    required = {"ip", "timestamp"}  # Relaxed requirements
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Dataset missing required columns: {missing}. "
            f"Please ensure your CSV has at least: ip and timestamp."
        )

    # Safe Type Handling
    # 1. Parse timestamps (Handles standard and Apache/Nginx formats)
    try:
        # Pre-process: Strip square brackets [ ] common in Apache/Nginx logs
        df["timestamp"] = df["timestamp"].astype(str).str.strip("[]")
        
        # Attempt 1: Standard parsing
        parsed_ts = pd.to_datetime(df["timestamp"], errors="coerce")
        
        # Attempt 2: Fallback to Apache format with timezone
        if parsed_ts.isna().mean() > 0.5:
            apache_format_tz = "%d/%b/%Y:%H:%M:%S %z"
            parsed_ts = pd.to_datetime(df["timestamp"], format=apache_format_tz, errors="coerce")

        # Attempt 3: Fallback to Apache format WITHOUT timezone
        if parsed_ts.isna().mean() > 0.5:
            apache_format_no_tz = "%d/%b/%Y:%H:%M:%S"
            parsed_ts = pd.to_datetime(df["timestamp"], format=apache_format_no_tz, errors="coerce")

        df["timestamp"] = parsed_ts

        if df["timestamp"].isna().all():
            raise ValueError("Timestamp parsing failed for all rows. Unsupported date format.")
    except Exception as e:
        if isinstance(e, ValueError) and "Timestamp parsing failed" in str(e):
            raise
        raise ValueError(f"Error parsing timestamps: {str(e)}")

    # 2. Parse status codes
    try:
        df["status"] = pd.to_numeric(df["status"], errors="coerce")
    except Exception as e:
        raise ValueError(f"Error parsing status codes: {str(e)}")

    # 3. Drop rows with invalid timestamp or status (essential for analysis)
    df = df.dropna(subset=["timestamp", "status"])
    if df.empty:
        raise ValueError("No valid rows remaining after filtering invalid timestamps or status codes.")

    # 4. Ensure correct types for downstream use
    df["status"] = df["status"].astype(int)
    
    # Sort by timestamp for windowing
    df = df.sort_values(by="timestamp").reset_index(drop=True)

    # -------------------------------------------------------------------------
    # STEP 3 — Create 5-Minute Time Windows
    # -------------------------------------------------------------------------
    try:
        grouped = df.groupby(
            ["ip", pd.Grouper(key="timestamp", freq="5min")],
            dropna=False,
        )
    except Exception as e:
        raise ValueError(f"Failed to group data by time windows: {str(e)}")

    # -------------------------------------------------------------------------
    # STEP 4 — Engineer Features For Each Group
    # -------------------------------------------------------------------------

    def _avg_time_gap_seconds(g: pd.DataFrame) -> float:
        """Mean seconds between consecutive requests within the group."""
        if len(g) < 2:
            return 0.0  # Default to 0 instead of NaN for better model handling
        g = g.sort_values("timestamp")
        diffs = g["timestamp"].diff().dt.total_seconds()
        return float(diffs.dropna().mean())

    # Aggregate base features
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
        else 1.0,
        axis=1,
    )
    features["request_rate_per_minute"] = features["total_requests"] / 5.0

    # Apply avg_time_gap_seconds per group and ensure alignment
    try:
        gap_series = grouped.apply(_avg_time_gap_seconds)
        # Ensure alignment by setting indices before joining
        features = features.set_index(["ip", "window_start"])
        features["avg_time_gap_seconds"] = gap_series
        features = features.reset_index()
    except Exception as e:
        raise ValueError(f"Feature engineering (time gaps) failed: {str(e)}")

    # -------------------------------------------------------------------------
    # STEP 5 — Return Clean Feature DataFrame
    # -------------------------------------------------------------------------
    cols_to_keep = [
        "ip",
        "window_start",
        "total_requests",
        "failed_requests",
        "success_ratio",
        "unique_endpoints",
        "request_rate_per_minute",
        "avg_time_gap_seconds",
    ]
    result = features[cols_to_keep].copy()

    result = result.fillna(0)
    result = result.reset_index(drop=True)

    # Ensure correct numeric types
    type_map = {
        "total_requests": int,
        "failed_requests": int,
        "unique_endpoints": int,
        "success_ratio": float,
        "request_rate_per_minute": float,
        "avg_time_gap_seconds": float
    }
    for col, t in type_map.items():
        result[col] = result[col].astype(t)

    return result
