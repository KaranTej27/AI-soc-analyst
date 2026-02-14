"""
FastAPI router for rendering analysis results.
"""

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """
    Render analysis results. Redirect to / if no results exist.
    """
    # -------------------------------------------------------------------------
    # STEP 1 — Check if analysis_results exists
    # -------------------------------------------------------------------------
    results = getattr(request.app.state, "analysis_results", None)
    if results is None:
        return RedirectResponse(url="/", status_code=303)

    # -------------------------------------------------------------------------
    # STEP 2 — Extract dataframe
    # -------------------------------------------------------------------------
    df = results

    # -------------------------------------------------------------------------
    # STEP 3 — Compute summary metrics
    # -------------------------------------------------------------------------
    total_ips = int(df["ip"].nunique())

    anomaly_label = df.get("anomaly_label")
    if anomaly_label is not None:
        total_anomalies = int((anomaly_label == -1).sum())
    else:
        total_anomalies = 0

    risk_level = df.get("risk_level")
    if risk_level is not None:
        high_risk_count = int((risk_level == "HIGH").sum())
    else:
        high_risk_count = 0

    risk_score = df.get("risk_score")
    avg_risk_score = 0.0
    risk_distribution = [0, 0, 0, 0, 0] # 5 bins: 0-20, 21-40, 41-60, 61-80, 81-100
    if risk_score is not None:
        avg_risk_score = float(risk_score.mean())
        if pd.isna(avg_risk_score):
            avg_risk_score = 0.0
        
        # Calculate distribution (ignoring NaNs)
        valid_scores = risk_score.dropna()
        for score in valid_scores:
            if score <= 20: risk_distribution[0] += 1
            elif score <= 40: risk_distribution[1] += 1
            elif score <= 60: risk_distribution[2] += 1
            elif score <= 80: risk_distribution[3] += 1
            else: risk_distribution[4] += 1
        
        # Convert counts to percentages for CSS height
        max_count = max(risk_distribution) if any(risk_distribution) else 1
        risk_distribution_pct = [(c / max_count) * 100 for c in risk_distribution]
    else:
        risk_distribution_pct = [0, 0, 0, 0, 0]

    metrics = {
        "total_ips": total_ips,
        "total_anomalies": total_anomalies,
        "high_risk_count": high_risk_count,
        "avg_risk_score": round(avg_risk_score, 2),
        "risk_distribution": risk_distribution_pct
    }

    # -------------------------------------------------------------------------
    # STEP 4 — Prepare Scatter Plot Data (Requests vs Failures)
    # -------------------------------------------------------------------------
    scatter_data = []
    if "total_requests" in df.columns and "failed_requests" in df.columns:
        # Avoid division by zero
        max_req = float(df["total_requests"].max())
        if pd.isna(max_req) or max_req <= 0: max_req = 1.0
        
        max_fail = float(df["failed_requests"].max())
        if pd.isna(max_fail) or max_fail <= 0: max_fail = 1.0
        
        for _, row in df.iterrows():
            # Normalize to 5-95% to keep dots within container visible area
            req = row["total_requests"] if not pd.isna(row["total_requests"]) else 0
            fail = row["failed_requests"] if not pd.isna(row["failed_requests"]) else 0
            
            scatter_data.append({
                "x": (req / max_req) * 90 + 5,
                "y": (fail / max_fail) * 90 + 5,
                "is_anomaly": row.get("anomaly_label") == -1,
                "ip": row["ip"]
            })

    # -------------------------------------------------------------------------
    # STEP 5 — Extract Model Insights
    # -------------------------------------------------------------------------
    algorithm = "Isolation Forest" if len(df) >= 50 else "Statistical Z-Score"
    
    top_threat = None
    if not df.empty and risk_score is not None and not risk_score.dropna().empty:
        try:
            top_idx = risk_score.idxmax()
            top_row = df.loc[top_idx]
            top_threat = {
                "ip": top_row["ip"],
                "risk_score": round(float(top_row["risk_score"]), 2),
                "anomaly": top_row.get("anomaly_label") == -1
            }
        except Exception:
            pass

    insights = {
        "algorithm": algorithm,
        "top_threat": top_threat,
        "window_size": "5 Minutes",
        "contamination": "Dynamic"
    }

    # -------------------------------------------------------------------------
    # STEP 6 — Convert dataframe to list of dicts
    # -------------------------------------------------------------------------
    records = df.to_dict(orient="records")

    # -------------------------------------------------------------------------
    # STEP 7 — Render logs.html
    # -------------------------------------------------------------------------
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={
            "metrics": metrics, 
            "records": records, 
            "scatter_data": scatter_data,
            "insights": insights
        },
    )