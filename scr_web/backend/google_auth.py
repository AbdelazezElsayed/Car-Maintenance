from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config
import os
from dotenv import load_dotenv
import json
import zlib
import random
import string
from datetime import datetime, timedelta, timezone
from jose import jwt
from pymongo import MongoClient
from typing import Optional

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongo:27017/CAR")
client = MongoClient(MONGODB_URI)
db = client['CAR']
users_collection = db['USER']

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Google OAuth2 settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/api/auth/google/callback")

# Configure OAuth
config = Config(environ=os.environ)
oauth = OAuth(config)

# Register Google provider
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid email profile",
        "redirect_uri": GOOGLE_REDIRECT_URI,
    },
)

# Create router
router = APIRouter()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.get("/google/login")
async def login_via_google(request: Request):
    """
    Redirect to Google OAuth2 login page
    """
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def auth_callback(request: Request):
    """
    Handle the callback from Google OAuth2
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not fetch user info from Google"
            )

        # Check if user exists in database
        email = user_info.get("email")
        user_doc = users_collection.find_one({"email": email})

        if not user_doc:
            # Generate verification code
            verification_code = ''.join(random.choices(string.digits, k=6))

            # Create new user
            user_data = {
                "name": user_info.get("name"),
                "email": email,
                "google_id": user_info.get("sub"),
                "picture": user_info.get("picture"),
                "is_google_auth": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "email_verified": False,
                "verification_code": verification_code,
                "verification_code_expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            }

            # In a real application, you would send an email with the verification code here
            # For now, we'll just print it to the console for testing
            print(f"Verification code for Google user {email}: {verification_code}")

            # Compress user data before saving
            compressed_data = zlib.compress(json.dumps(user_data).encode('utf-8'))
            users_collection.insert_one({"email": email, "data": compressed_data})
        else:
            # Update existing user with Google info
            user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))
            user["google_id"] = user_info.get("sub")
            user["picture"] = user_info.get("picture")
            user["is_google_auth"] = True
            user["last_login"] = datetime.now(timezone.utc).isoformat()

            # Compress and update user data
            compressed_data = zlib.compress(json.dumps(user).encode('utf-8'))
            users_collection.update_one(
                {"email": email},
                {"$set": {"data": compressed_data}}
            )

        # Get user data to check if email is verified
        user_doc = users_collection.find_one({"email": email})
        user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))

        # Check if email is verified
        if not user.get("email_verified", False):
            # Redirect to verification page
            return RedirectResponse(url=f"/verify-email?email={email}")

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email},
            expires_delta=access_token_expires
        )

        # Redirect to frontend with token
        frontend_url = "http://localhost:8080/auth-success"
        redirect_url = f"{frontend_url}?token={access_token}"

        return RedirectResponse(url=redirect_url)

    except OAuthError as error:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"OAuth error: {error.error}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Authentication failed: {str(e)}"}
        )

@router.get("/google/user")
async def get_user_info(request: Request):
    """
    Get user info from Google
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get("userinfo")
        return user
    except OAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error.error}"
        )
