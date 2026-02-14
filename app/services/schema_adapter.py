"""
Universal CSV schema detection and standardization engine.
Pure Python module — no FastAPI imports.
"""

import pandas as pd
import numpy as np


def detect_and_standardize_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize a dataframe's schema by normalizing column names,
    detecting common variants, and providing default values for missing required fields.
    
    Requirements:
    1. Normalize column names (strip, lowercase).
    2. Automatically detect common variants for: ip, timestamp, status, endpoint.
    3. Variants:
       ip: ip_address, source_ip, client_ip
       timestamp: time, datetime, event_time
       status: response_code, status_code
       endpoint: url, uri, path, request
    4. Missing ip -> "global"
    5. Missing timestamp -> ValueError
    6. Missing status -> 200
    7. Missing endpoint -> "unknown"
    """
    
    # 1. Normalize column names
    df.columns = df.columns.astype(str).str.strip().str.lower()
    
    # 2 & 3. Column variants mapping
    variants = {
        "ip": ["ip_address", "source_ip", "client_ip"],
        "timestamp": ["time", "datetime", "event_time"],
        "status": ["response_code", "status_code"],
        "endpoint": ["url", "uri", "path", "request"]
    }
    
    # Identify which mapped columns already exist
    existing_cols = set(df.columns)
    
    # Mapping to perform
    mapping = {}
    
    for target, variant_list in variants.items():
        # If target already exists, skip
        if target in existing_cols:
            continue
            
        # Check for variants
        for variant in variant_list:
            if variant in existing_cols:
                mapping[variant] = target
                break # Take the first variant found
                
    if mapping:
        df = df.rename(columns=mapping)
        
    # 4-7. Default values and validation
    
    # Timestamp is strictly required
    if "timestamp" not in df.columns:
        raise ValueError("Critical error: 'timestamp' column is missing and no variants were found.")
        
    # Add defaults if missing
    if "ip" not in df.columns:
        df["ip"] = "global"
        
    if "status" not in df.columns:
        df["status"] = 200
        
    if "endpoint" not in df.columns:
        df["endpoint"] = "unknown"
        
    return df
