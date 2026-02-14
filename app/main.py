from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes.upload import router as upload_router
from app.routes.detect import router as detect_router
import os

app = FastAPI(title="AI SOC Analyst")

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Configure templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include routers
app.include_router(upload_router)
app.include_router(detect_router)

@app.get("/", tags=["UI"])
async def read_root(request: Request):
    """Render the onboarding screen."""
    return templates.TemplateResponse("onboard.html", {"request": request})

@app.get("/about", tags=["UI"])
async def read_about(request: Request):
    """Render the about page."""
    return templates.TemplateResponse("about.html", {"request": request})
