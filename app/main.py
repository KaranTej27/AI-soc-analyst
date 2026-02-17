from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes.upload import router as upload_router
from app.routes.detect import router as detect_router
from app.database.db import DatabaseManager
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
    """Render the public landing page (about page)."""
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/about", tags=["UI"])
async def read_about(request: Request):
    """Render the about page."""
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/login", tags=["Auth"])
async def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", tags=["Auth"])
async def signup_page(request: Request):
    """Render the signup page."""
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/login", tags=["Auth"])
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    """Handle login authentication."""
    # Note: 'email' field in form is used for either username or email identifier
    user = DatabaseManager.get_user_by_identifier(email)
    
    if user and DatabaseManager.verify_password(password, user['password_hash']):
        # Success: Redirect to dashboard
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        # Failure: Re-render login with error
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid username/email or password."}
        )

@app.post("/signup", tags=["Auth"])
async def signup_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    """Handle new user registration."""
    user_id = DatabaseManager.create_user(username, email, password)
    
    if user_id:
        # Success: Redirect to login
        return RedirectResponse(url="/login", status_code=303)
    else:
        # Failure: Re-render signup with error
        return templates.TemplateResponse(
            "signup.html", 
            {"request": request, "error": "Registration failed. Username or Email may already exist."}
        )

@app.get("/dashboard", tags=["UI"])
async def dashboard(request: Request):
    """Render the main dashboard (onboarding view)."""
    return templates.TemplateResponse("onboard.html", {"request": request})

@app.get("/onboard", tags=["UI"])
async def onboard_redirect():
    """Redirect legacy onboard route to dashboard."""
    return RedirectResponse(url="/dashboard")
