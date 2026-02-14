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
    if risk_score is not None:
        avg_risk_score = float(risk_score.mean())
        if pd.isna(avg_risk_score):
            avg_risk_score = 0.0
    else:
        avg_risk_score = 0.0

    metrics = {
        "total_ips": total_ips,
        "total_anomalies": total_anomalies,
        "high_risk_count": high_risk_count,
        "avg_risk_score": round(avg_risk_score, 2),
    }

    # -------------------------------------------------------------------------
    # STEP 4 — Convert dataframe to list of dicts
    # -------------------------------------------------------------------------
    records = df.to_dict(orient="records")

    # -------------------------------------------------------------------------
    # STEP 5 — Render logs.html
    # -------------------------------------------------------------------------
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={"metrics": metrics, "records": records},
    )
