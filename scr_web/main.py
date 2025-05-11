from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from backend.auth import router as auth_router, startup_create_admin
from backend.gemini_chat import router as gemini_router
from backend.tire_analysis import router as tire_router
from backend.maintenance import router as maintenance_router
import os
import sys
import time
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Get secret key from environment
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://carcare_mongo:27017/CAR")

# Connect to MongoDB using the modern lifespan approach
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    try:
        # Check if we're in development mode (running with uvicorn directly)
        is_dev_mode = os.environ.get("UVICORN_RELOAD", "0") == "1" or "--reload" in sys.argv

        if is_dev_mode:
            # Use a simpler connection string for development without authentication
            dev_uri = "mongodb://localhost:27017/CAR"
            print("Running in development mode, using local MongoDB without auth")
            app.mongodb_client = MongoClient(dev_uri, serverSelectionTimeoutMS=5000)
        else:
            # Use the configured URI with authentication for production
            print(f"Connecting to MongoDB using URI: {MONGODB_URI}")
            app.mongodb_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

        # Verify the connection
        app.mongodb_client.admin.command('ping')
        app.database = app.mongodb_client.get_database("CAR")
        print("Connected to MongoDB successfully")

        # Create admin user
        try:
            await startup_create_admin()
            print("Admin user creation process completed")
        except Exception as e:
            print(f"Error during admin user creation: {str(e)}")
            # Continue even if admin creation fails

    except Exception as e:
        print(f"Failed to connect to MongoDB: {str(e)}")
        # We'll continue and let the health check handle this

    yield  # This is where the app runs

    # Shutdown: Close MongoDB connection
    if hasattr(app, "mongodb_client"):
        app.mongodb_client.close()
        print("MongoDB connection closed")

# Initialize FastAPI app
app = FastAPI(
    title="CarCare Pro API",
    description="API for CarCare Pro application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# In Docker, we don't need to mount static files from the backend
# The frontend container serves all static files
# These mounts are only used when running without Docker

# Check if frontend directory exists before mounting
import os
if os.path.exists("frontend"):
    # Mount the frontend directory for static files
    app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

    # Mount the styles directory for CSS files
    if os.path.exists("frontend/styles"):
        app.mount("/styles", StaticFiles(directory="frontend/styles"), name="styles")

    # Mount the scripts directory for JavaScript files
    if os.path.exists("frontend/scripts"):
        app.mount("/scripts", StaticFiles(directory="frontend/scripts"), name="scripts")

    # Mount the frontend assets directory
    if os.path.exists("frontend/assets"):
        app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# Include the routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(gemini_router, prefix="/api/gemini")
app.include_router(tire_router, prefix="/api/tire")
app.include_router(maintenance_router, prefix="/api/maintenance")

# Admin user creation is now handled in the lifespan context manager

# Add a route for the API root
@app.get("/api", response_class=HTMLResponse)
async def api_root():
    """
    API root endpoint that provides information about available endpoints
    """
    try:
        with open("backend/api_index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Fallback to JSON response if HTML file is not found
        return {
            "name": "CarCare Pro API",
            "version": "1.0.0",
            "description": "API for CarCare Pro application",
            "endpoints": {
                "health": {
                    "url": "/api/health",
                    "description": "Health check endpoint"
                },
                "auth": {
                    "url": "/api/auth",
                    "description": "Authentication endpoints"
                },
                "gemini": {
                    "url": "/api/gemini",
                    "description": "Gemini AI chat endpoints"
                },
                "tire": {
                    "url": "/api/tire",
                    "description": "Tire analysis endpoints"
                },
                "maintenance": {
                    "url": "/api/maintenance",
                    "description": "Maintenance tracking endpoints"
                }
            },
            "documentation": {
                "swagger": "/api/docs",
                "redoc": "/api/redoc",
                "openapi": "/api/openapi.json"
            }
        }

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/index")

@app.get("/index", response_class=HTMLResponse)
async def index_page():
    try:
        with open("frontend/pages/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Index page not found")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    try:
        with open("frontend/pages/login/login.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Login page not found")

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    try:
        with open("frontend/pages/register/register.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Registration page not found")

@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    try:
        with open("frontend/pages/chat/chat.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chat page not found")

@app.get("/tire", response_class=HTMLResponse)
async def tire_page():
    try:
        with open("frontend/pages/tire/tire.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Tire page not found")

@app.get("/maintenance", response_class=HTMLResponse)
async def maintenance_page():
    try:
        with open("frontend/pages/maintenance/maintenance.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Maintenance page not found")

@app.get("/auth-success", response_class=HTMLResponse)
async def auth_success_page():
    try:
        with open("frontend/pages/auth-success/auth-success.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Auth success page not found")

@app.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page():
    try:
        with open("frontend/pages/verify-email/verify-email.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Verify email page not found")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    try:
        with open("frontend/pages/admin/admin.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Admin page not found")

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for monitoring and container orchestration
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "api": "up",
            "database": "unknown",
            "gemini_api": "unknown"
        },
        "mode": "development" if os.environ.get("UVICORN_RELOAD", "0") == "1" or "--reload" in sys.argv else "production"
    }

    # Check MongoDB connection
    try:
        if hasattr(app, "mongodb_client"):
            app.mongodb_client.admin.command('ping')
            health_status["services"]["database"] = "up"
        else:
            health_status["services"]["database"] = "down"
            # In development mode, we'll still return a 200 status
            if health_status["mode"] == "development":
                health_status["status"] = "development"
                health_status["message"] = "Database connection not available, but running in development mode"
            else:
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["database"] = "down"
        error_message = str(e)

        # In development mode, we'll still return a 200 status
        if health_status["mode"] == "development":
            health_status["status"] = "development"
            health_status["message"] = f"Database error in development mode: {error_message}"
            health_status["error"] = error_message
        else:
            health_status["status"] = "degraded"
            health_status["error"] = error_message
            return JSONResponse(status_code=503, content=health_status)

    # Check Gemini API key
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv

        # Load environment variables
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            health_status["services"]["gemini_api"] = "down"
            health_status["gemini_api_error"] = "API key not found in .env file"
        else:
            # Configure Gemini
            genai.configure(api_key=api_key)

            # List available models
            models = genai.list_models()
            gemini_models = [model.name for model in models if "gemini" in model.name.lower()]

            if gemini_models:
                health_status["services"]["gemini_api"] = "up"
                health_status["gemini_models"] = gemini_models
            else:
                health_status["services"]["gemini_api"] = "degraded"
                health_status["gemini_api_error"] = "No Gemini models found"
    except Exception as e:
        health_status["services"]["gemini_api"] = "down"
        health_status["gemini_api_error"] = str(e)

        # Don't fail the health check for Gemini API issues in development mode
        if health_status["mode"] == "development" and health_status["services"]["database"] == "up":
            health_status["status"] = "development"
            if not "message" in health_status:
                health_status["message"] = "Gemini API issues in development mode"

    return health_status

@app.exception_handler(404)
async def not_found_handler(*_):
    """Handle 404 errors with a custom response"""
    return HTMLResponse(content="404 - Page not found", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)