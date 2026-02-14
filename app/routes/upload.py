"""
FastAPI router for CSV upload and anomaly detection pipeline.
"""

import os
import shutil
import uuid
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse

from app.services.preprocessing import build_features
from app.services.model import run_isolation_forest
from app.services.risk import assign_risk_levels

router = APIRouter()

# Directory for temporary uploads
UPLOAD_DIR = "data"


@router.post("/upload")
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Accept CSV upload, run anomaly pipeline, store results, and redirect to /logs.
    """
    file_path = None

    try:
        # ---------------------------------------------------------------------
        # STEP 1 — Accept CSV file upload
        # ---------------------------------------------------------------------
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a CSV file.",
            )

        # ---------------------------------------------------------------------
        # STEP 2 — Save file temporarily to data/ directory
        # ---------------------------------------------------------------------
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # ---------------------------------------------------------------------
        # STEP 3 — Run full pipeline
        # ---------------------------------------------------------------------
        df = build_features(file_path)
        df = run_isolation_forest(df)
        df = assign_risk_levels(df)

        # ---------------------------------------------------------------------
        # STEP 4 — Store result in memory
        # ---------------------------------------------------------------------
        if not hasattr(request.app.state, "analysis_results"):
            request.app.state.analysis_results = None
        request.app.state.analysis_results = df

        # ---------------------------------------------------------------------
        # STEP 5 — Redirect to /logs
        # ---------------------------------------------------------------------
        return RedirectResponse(url="/logs", status_code=303)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}",
        )
    finally:
        # Clean up temporary file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
