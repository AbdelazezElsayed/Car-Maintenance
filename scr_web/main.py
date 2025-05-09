from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.auth import router as auth_router
from backend.gemini_chat import router as gemini_router
from backend.tire_analysis import router as tire_router
import os

app = FastAPI()

# Mount the frontend directory for static files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Mount the styles directory for CSS files
app.mount("/styles", StaticFiles(directory="frontend/styles"), name="styles")

# Mount the frontend assets directory
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# Include the routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(gemini_router, prefix="/api/gemini")
app.include_router(tire_router, prefix="/api/tire")

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

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return HTMLResponse(content="404 - Page not found", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 