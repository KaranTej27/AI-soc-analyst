"""
FastAPI router for CSV upload and anomaly detection pipeline.
Enhanced with rigid validation, performance logging, and adaptive error handling.
"""

import os
import shutil
import uuid
import time
import logging
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, JSONResponse

from app.services.preprocessing import build_features
from app.services.model import run_isolation_forest
from app.services.risk import assign_risk_levels

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Directory for temporary uploads
UPLOAD_DIR = "data"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload")
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Accept CSV upload, run anomaly pipeline, store results, and redirect or return JSON.
    """
    file_path = None
    start_time = time.perf_counter()
    
    # helper for adaptive error handling
    def _error_response(status_code: int, detail: str):
        if "application/json" in request.headers.get("Accept", ""):
            return JSONResponse(status_code=status_code, content={"status": "error", "message": detail})
        raise HTTPException(status_code=status_code, detail=detail)

    try:
        # ---------------------------------------------------------------------
        # STEP 1 — Validate File (Size & Type)
        # ---------------------------------------------------------------------
        # 1. Reject non-CSV files
        if not file.filename or not file.filename.lower().endswith(".csv"):
            return _error_response(400, "Invalid file type. Please upload a CSV file.")

        # 2. Reject files larger than 50MB
        file_size = getattr(file, "size", 0)
        if file_size == 0:
            try:
                await file.seek(0, 2)
                file_size = await file.tell()
                await file.seek(0)
            except Exception:
                pass

        if file_size > MAX_FILE_SIZE:
            return _error_response(413, f"File too large. Maximum allowed size is 50MB.")

        # ---------------------------------------------------------------------
        # STEP 2 — Save file temporarily to data/ directory
        # ---------------------------------------------------------------------
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # ---------------------------------------------------------------------
        # STEP 3 — Run full pipeline with performance tracking
        # ---------------------------------------------------------------------
        
        # Performance Tracking: Feature Engineering
        fe_start = time.perf_counter()
        df = build_features(file_path)
        fe_duration = time.perf_counter() - fe_start
        
        rows_processed = len(df) if df is not None else 0

        # Performance Tracking: Model Inference
        inference_start = time.perf_counter()
        df = run_isolation_forest(df)
        df = assign_risk_levels(df)
        inference_duration = time.perf_counter() - inference_start
        
        total_duration = time.perf_counter() - start_time

        # ---------------------------------------------------------------------
        # STEP 4 — Logging
        # ---------------------------------------------------------------------
        logger.info(
            f"Upload successful: {file.filename} | "
            f"Size: {file_size / 1024:.2f} KB | "
            f"Rows: {rows_processed} | "
            f"FE Time: {fe_duration:.4f}s | "
            f"Model Time: {inference_duration:.4f}s | "
            f"Total Time: {total_duration:.4f}s"
        )

        # ---------------------------------------------------------------------
        # STEP 5 — Store result in memory
        # ---------------------------------------------------------------------
        if not hasattr(request.app.state, "analysis_results"):
            request.app.state.analysis_results = None
        request.app.state.analysis_results = df

        # ---------------------------------------------------------------------
        # STEP 6 — Adaptive Response
        # ---------------------------------------------------------------------
        if "application/json" in request.headers.get("Accept", ""):
            return {
                "status": "success",
                "message": "Detection completed successfully.",
                "metrics": {
                    "file_size_kb": round(file_size / 1024, 2),
                    "rows_processed": rows_processed,
                    "fe_time_sec": round(fe_duration, 4),
                    "model_time_sec": round(inference_duration, 4),
                    "total_time_sec": round(total_duration, 4)
                }
            }
        
        return RedirectResponse(url="/logs", status_code=303)

    except HTTPException as he:
        # Re-raise or return the specific error response
        if "application/json" in request.headers.get("Accept", ""):
            return JSONResponse(status_code=he.status_code, content={"status": "error", "message": he.detail})
        raise he

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return _error_response(500, str(e))
        
    finally:
        # Clean up temporary file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
