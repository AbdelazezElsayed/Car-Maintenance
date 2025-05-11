from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
from dotenv import load_dotenv
import zlib
import json
import random
import string

load_dotenv()

# MongoDB connection to CAR.USER
# Get MongoDB URI from environment variable or use default
# For local development, use localhost
# For Docker environment, use the container name 'carcare_mongo'
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://carcare_mongo:27017/CAR")

# Check if we're running in Docker environment
if os.path.exists('/.dockerenv'):
    print("Running in Docker environment")
else:
    # If not in Docker and URI contains 'mongo', try localhost instead
    if 'mongo' in MONGODB_URI and not os.path.exists('/.dockerenv'):
        MONGODB_URI = MONGODB_URI.replace('mongo', 'localhost')
        print(f"Not in Docker, using local MongoDB: {MONGODB_URI}")

# Connect to MongoDB
try:
    print(f"Connecting to MongoDB with URI: {MONGODB_URI}")
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Ping the server to check connection
    client.admin.command('ping')
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    # Fallback to localhost if connection fails
    if 'mongo' in MONGODB_URI:
        fallback_uri = MONGODB_URI.replace('mongo', 'localhost')
        try:
            print(f"Trying fallback connection: {fallback_uri}")
            client = MongoClient(fallback_uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            print("Connected to MongoDB using fallback connection!")
            MONGODB_URI = fallback_uri
        except Exception as e2:
            print(f"Failed to connect using fallback: {e2}")

# Get database and collection
db = client['CAR']
users_collection = db['USER']

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-keep-it-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class UserRole:
    USER = "user"
    ADMIN = "admin"

class User(BaseModel):
    name: str
    email: EmailStr
    password: Optional[str] = None
    google_id: Optional[str] = None
    picture: Optional[str] = None
    is_google_auth: bool = False
    verification_code: Optional[str] = None
    email_verified: bool = False
    role: str = UserRole.USER

class LoginRequest(BaseModel):
    username: str
    password: str

class GoogleAuthRequest(BaseModel):
    token: str

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

class ResendCodeRequest(BaseModel):
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: Optional[dict] = None

class TokenData(BaseModel):
    email: str | None = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def generate_verification_code(length=6):
    """Generate a random verification code"""
    return ''.join(random.choices(string.digits, k=length))

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user_doc = users_collection.find_one({"email": token_data.email})
    if user_doc is None:
        raise credentials_exception
    # Decompress user data
    user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))
    return user

async def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized. Admin privileges required."
        )
    return current_user

# FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIRouter
router = APIRouter()

@router.post("/register")
async def register(user: User):
    # Check if email already exists
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_dict = user.model_dump()

    # If it's a regular registration (not Google auth)
    if not user.is_google_auth and user.password:
        hashed_password = get_password_hash(user.password)
        user_dict["password"] = hashed_password

    # Generate verification code
    verification_code = generate_verification_code()

    # Add registration timestamp and verification info
    user_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    user_dict["email_verified"] = False  # Default to email not verified
    user_dict["verification_code"] = verification_code
    user_dict["verification_code_expires"] = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    # Compress user data before saving
    compressed_data = zlib.compress(json.dumps(user_dict).encode('utf-8'))

    try:
        # Insert the new user
        result = users_collection.insert_one({"email": user.email, "data": compressed_data})

        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to register user")

        # Send verification email
        from backend.email_service import send_verification_email
        send_verification_email(user.email, verification_code)

        return {
            "message": "User registered successfully. Please check your email for verification code.",
            "email": user.email,
            "redirect_to": f"/verify-email?email={user.email}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    user_doc = users_collection.find_one({"email": login_data.username})
    if not user_doc:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Decompress user data
    user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))

    # Check if this is a Google authenticated user without a password
    if user.get("is_google_auth") and not user.get("password"):
        raise HTTPException(
            status_code=401,
            detail="This account uses Google Sign-In. Please login with Google.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if email is verified
    if not user.get("email_verified", False):
        # Redirect to verification page
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please verify your email before logging in.",
            headers={"X-Redirect": f"/verify-email?email={user.get('email')}"}
        )

    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login time
    user["last_login"] = datetime.now(timezone.utc).isoformat()
    compressed_data = zlib.compress(json.dumps(user).encode('utf-8'))
    users_collection.update_one(
        {"email": user["email"]},
        {"$set": {"data": compressed_data}}
    )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )

    # Return user info without sensitive data
    user_info = {
        "name": user.get("name"),
        "email": user.get("email"),
        "picture": user.get("picture"),
        "is_google_auth": user.get("is_google_auth", False),
        "role": user.get("role", UserRole.USER)
    }

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": user_info
    }

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    user_doc = users_collection.find_one({"email": current_user.get("email")})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))
    user_data = {
        "name": user.get("name"),
        "email": user.get("email"),
        "picture": user.get("picture"),
        "is_google_auth": user.get("is_google_auth", False),
        "role": user.get("role", UserRole.USER),
        "last_login": user.get("last_login"),
        "created_at": user.get("created_at")
    }
    return user_data

@router.post("/verify-code")
async def verify_code(verify_data: VerifyCodeRequest):
    """
    Verify user email with the provided verification code
    """
    try:
        # Find the user
        user_doc = users_collection.find_one({"email": verify_data.email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user data
        user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))

        # Check if already verified
        if user.get("email_verified", False):
            return {"message": "Email already verified", "redirect_to": "/login?verified=true"}

        # Check verification code
        stored_code = user.get("verification_code")
        if not stored_code:
            raise HTTPException(status_code=400, detail="No verification code found. Please request a new one.")

        # Check if code has expired
        expires_str = user.get("verification_code_expires")
        if expires_str:
            expires = datetime.fromisoformat(expires_str)
            if datetime.now(timezone.utc) > expires:
                raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")

        # Verify the code
        if verify_data.code != stored_code:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        # Update user's email_verified status
        user["email_verified"] = True
        user["verification_code"] = None  # Clear the code after successful verification
        user["verification_code_expires"] = None

        # Save the updated user data
        compressed_data = zlib.compress(json.dumps(user).encode('utf-8'))
        users_collection.update_one(
            {"email": verify_data.email},
            {"$set": {"data": compressed_data}}
        )

        return {"message": "Email verified successfully", "redirect_to": "/login?verified=true"}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.post("/resend-code")
async def resend_verification_code(resend_data: ResendCodeRequest):
    """
    Resend verification code to the user's email
    """
    try:
        # Find the user
        user_doc = users_collection.find_one({"email": resend_data.email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user data
        user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))

        # Check if already verified
        if user.get("email_verified", False):
            return {"message": "Email already verified", "redirect_to": "/login?verified=true"}

        # Generate new verification code
        verification_code = generate_verification_code()

        # Update verification info
        user["verification_code"] = verification_code
        user["verification_code_expires"] = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

        # Save the updated user data
        compressed_data = zlib.compress(json.dumps(user).encode('utf-8'))
        users_collection.update_one(
            {"email": resend_data.email},
            {"$set": {"data": compressed_data}}
        )

        # Send verification email
        from backend.email_service import send_verification_email
        send_verification_email(resend_data.email, verification_code)

        return {"message": "Verification code resent. Please check your email."}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to resend verification code: {str(e)}")

# Admin-only endpoints
@router.post("/admin/register", dependencies=[Depends(get_current_admin)])
async def admin_register_user(user: User):
    """
    Register a new user with admin privileges (admin-only endpoint)
    """
    # Check if email already exists
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_dict = user.model_dump()

    # Set role to admin
    user_dict["role"] = UserRole.ADMIN

    # If password is provided, hash it
    if user.password:
        hashed_password = get_password_hash(user.password)
        user_dict["password"] = hashed_password

    # Set email as verified for admin users
    user_dict["email_verified"] = True
    user_dict["created_at"] = datetime.now(timezone.utc).isoformat()

    # Compress user data before saving
    compressed_data = zlib.compress(json.dumps(user_dict).encode('utf-8'))

    try:
        # Insert the new admin user
        result = users_collection.insert_one({"email": user.email, "data": compressed_data})

        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to register admin user")

        return {"message": f"Admin user {user.email} registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Admin registration failed: {str(e)}")

@router.get("/admin/users", dependencies=[Depends(get_current_admin)])
async def get_all_users():
    """
    Get all users (admin-only endpoint)
    """
    try:
        users = []
        for user_doc in users_collection.find():
            user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))
            # Remove sensitive data
            if "password" in user:
                del user["password"]
            if "verification_code" in user:
                del user["verification_code"]
            users.append(user)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@router.get("/admin/test-email", dependencies=[Depends(get_current_admin)])
async def test_email_configuration():
    """
    Test email configuration (admin-only endpoint)
    """
    try:
        from backend.email_service import test_email_configuration
        result = test_email_configuration()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test email configuration: {str(e)}")

# Function to create the first admin user if none exists
async def create_first_admin():
    """
    Create the first admin user if no admin exists
    """
    # Check if any admin user exists
    admin_exists = False
    for user_doc in users_collection.find():
        user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))
        if user.get("role") == UserRole.ADMIN:
            admin_exists = True
            break

    if not admin_exists:
        # Create default admin user
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

        # Check if the email is already registered
        if users_collection.find_one({"email": admin_email}):
            # Update existing user to admin
            user_doc = users_collection.find_one({"email": admin_email})
            user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))
            user["role"] = UserRole.ADMIN
            user["email_verified"] = True
            compressed_data = zlib.compress(json.dumps(user).encode('utf-8'))
            users_collection.update_one(
                {"email": admin_email},
                {"$set": {"data": compressed_data}}
            )
            print(f"Existing user {admin_email} upgraded to admin")
        else:
            # Create new admin user
            hashed_password = get_password_hash(admin_password)
            admin_user = {
                "name": "Admin",
                "email": admin_email,
                "password": hashed_password,
                "role": UserRole.ADMIN,
                "email_verified": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            compressed_data = zlib.compress(json.dumps(admin_user).encode('utf-8'))
            users_collection.insert_one({"email": admin_email, "data": compressed_data})
            print(f"Created default admin user: {admin_email}")

# Create first admin user on startup
import asyncio

# We'll create a startup event handler in FastAPI to run this
# The function will be called by FastAPI when the app starts
# This avoids the "no running event loop" error

# Define a function to be called on startup
async def startup_create_admin():
    try:
        await create_first_admin()
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")

# The actual registration of this function happens in main.py

# Development-only endpoints
class DevEmailRequest(BaseModel):
    email: EmailStr

@router.post("/dev/get-verification-code")
async def get_verification_code_dev(request: DevEmailRequest):
    """
    Development-only endpoint to retrieve verification code for testing
    This should NEVER be used in production
    """
    # Check if we're in development mode
    import sys
    is_dev_mode = os.environ.get("UVICORN_RELOAD", "0") == "1" or "--reload" in sys.argv

    if not is_dev_mode:
        raise HTTPException(status_code=403, detail="This endpoint is only available in development mode")

    try:
        # Find the user
        user_doc = users_collection.find_one({"email": request.email})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user data
        user = json.loads(zlib.decompress(user_doc["data"]).decode('utf-8'))

        # Check if already verified
        if user.get("email_verified", False):
            return {"message": "Email already verified"}

        # Return verification code
        verification_code = user.get("verification_code")
        if not verification_code:
            raise HTTPException(status_code=400, detail="No verification code found. Please request a new one.")

        return {"verification_code": verification_code}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to retrieve verification code: {str(e)}")

# Add Google authentication endpoints
from backend.google_auth import router as google_router
router.include_router(google_router, prefix="/google")

# Include router
app.include_router(router)