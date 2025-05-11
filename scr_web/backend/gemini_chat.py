from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging
from typing import Optional, List, Dict
import time
from backend.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("Gemini API key not found in .env file")

# Define safety settings
SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

# Define generation config
GENERATION_CONFIG = {
    'temperature': 0.7,
    'top_p': 0.8,
    'top_k': 40,
    'max_output_tokens': 2048,
}

# Configure Gemini with retry mechanism
def initialize_gemini(max_retries=3, retry_delay=2):
    for attempt in range(max_retries):
        try:
            genai.configure(api_key=GEMINI_API_KEY)

            # Initialize model with safety settings
            # Use gemini-1.0-pro or gemini-1.5-pro based on availability
            available_models = genai.list_models()
            model_names = [model.name for model in available_models]

            # Choose the best available model, prioritizing free models
            if "models/gemini-1.5-flash" in model_names:
                model_name = "gemini-1.5-flash"  # Free model
            elif "models/gemini-1.0-pro-vision" in model_names:
                model_name = "gemini-1.0-pro-vision"  # Free model
            elif "models/gemini-1.0-pro" in model_names:
                model_name = "gemini-1.0-pro"
            elif "models/gemini-pro" in model_names:
                model_name = "gemini-pro"
            else:
                # Try any available model with "gemini" in the name
                gemini_models = [name for name in model_names if "gemini" in name.lower()]
                if gemini_models:
                    model_name = gemini_models[0].replace("models/", "")
                else:
                    model_name = "gemini-pro"  # Fallback to original name

            logger.info(f"Using Gemini model: {model_name}")

            model = genai.GenerativeModel(
                model_name,
                generation_config=GENERATION_CONFIG,
                safety_settings=SAFETY_SETTINGS
            )

            # Test the model with a simple query to ensure it's working
            test_response = model.generate_content("Hello")
            if test_response and hasattr(test_response, 'text'):
                logger.info("Gemini API initialized successfully with safety settings")
                return model
            else:
                raise ValueError("Model returned invalid response during initialization test")

        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to initialize Gemini API after {max_retries} attempts: {str(e)}")
                raise RuntimeError(f"Failed to initialize Gemini API: {str(e)}")

# Initialize the model
try:
    model = initialize_gemini()
except Exception as e:
    logger.error(f"Critical error initializing Gemini API: {str(e)}")
    model = None  # We'll handle this in the endpoint by reinitializing if needed

# Fallback responses for when the API is unavailable
FALLBACK_RESPONSES = {
    "general": "I'm sorry, but I'm currently unable to access my automotive knowledge database. "
               "Please try again later or contact support if the issue persists.",
    "maintenance": "I apologize, but I can't provide maintenance advice at the moment due to a technical issue. "
                  "For urgent maintenance questions, please consult your vehicle's manual or contact a certified mechanic.",
    "diagnostic": "I'm experiencing a technical issue and can't help with diagnostics right now. "
                 "If you're experiencing car problems, please consult a professional mechanic for assistance.",
    "recommendation": "I'm sorry, but I can't provide vehicle recommendations at the moment. "
                     "Please try again later when my systems are back online."
}

def get_fallback_response(query):
    """Provide a fallback response when the Gemini API is unavailable"""
    query = query.lower()

    if any(word in query for word in ["maintain", "maintenance", "service", "oil", "filter", "change"]):
        return FALLBACK_RESPONSES["maintenance"]
    elif any(word in query for word in ["problem", "issue", "diagnose", "diagnostic", "check", "light", "warning"]):
        return FALLBACK_RESPONSES["diagnostic"]
    elif any(word in query for word in ["recommend", "suggestion", "buy", "purchase", "best", "compare"]):
        return FALLBACK_RESPONSES["recommendation"]
    else:
        return FALLBACK_RESPONSES["general"]

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    context: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str

# System prompt to guide the model's behavior
SYSTEM_PROMPT = """
You are an automotive expert assistant for CarCare Pro, a car maintenance and advice application.
Your role is to provide helpful, accurate information about:
- Car maintenance and repair
- Vehicle diagnostics and troubleshooting
- Car buying advice and comparisons
- General automotive knowledge

Always be polite, concise, and focus on providing practical advice.
If you're unsure about something, acknowledge it rather than providing potentially incorrect information.
Avoid discussing topics unrelated to automotive matters.
"""

@router.post("/chat", response_model=ChatResponse)
async def chat_with_gemini(req: ChatRequest, _: dict = Depends(get_current_user)):
    # The current_user dependency is used for authentication but not needed in the function body
    """
    Chat with Gemini API with authentication and improved error handling
    """
    global model  # Use the global model instance

    # Validate input
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Prepare the message with automotive context
    user_message = req.message.strip()

    # Add automotive context to the user's query
    prompt = f"{SYSTEM_PROMPT}\n\nUser query: {user_message}"

    # Retry mechanism for API calls
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            # Check if model is initialized, if not, initialize it
            if 'model' not in globals() or model is None:
                logger.warning("Model not initialized, attempting to initialize now")
                model = initialize_gemini()

            logger.info(f"Sending request to Gemini API (attempt {attempt+1}/{max_retries}): {user_message[:50]}...")

            # Generate response with safety settings
            response = model.generate_content(prompt)

            # Validate response
            if not response or not hasattr(response, 'text') or not response.text:
                if attempt < max_retries - 1:
                    logger.warning(f"Empty response from Gemini API on attempt {attempt+1}, retrying...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error("Empty or invalid response from Gemini API after all retries")
                    raise HTTPException(status_code=500, detail="Invalid response from Gemini")

            # Log success and return response
            logger.info(f"Successfully received response from Gemini API on attempt {attempt+1}")
            return {"response": response.text}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in chat_with_gemini (attempt {attempt+1}): {error_msg}")

            # Handle specific error cases
            if "404" in error_msg and "models/" in error_msg:
                # Model not found - try to reinitialize with a different model
                logger.warning(f"Model not found error: {error_msg}")
                if attempt < max_retries - 1:
                    logger.info("Attempting to reinitialize with a different model")
                    # Force reinitialization
                    model = None
                    time.sleep(retry_delay)
                    continue
                else:
                    raise HTTPException(status_code=500, detail="AI model unavailable. Please try again later.")
            elif "400" in error_msg:
                # Bad request - no need to retry
                raise HTTPException(status_code=400, detail="Invalid request to AI service")
            elif "429" in error_msg:
                # Rate limit - wait longer before retry
                if attempt < max_retries - 1:
                    logger.warning(f"Rate limit exceeded, waiting before retry {attempt+1}")
                    time.sleep(retry_delay * 2)  # Wait longer for rate limit errors
                    continue
                else:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
            elif "503" in error_msg or "500" in error_msg:
                # Server error - retry with backoff
                if attempt < max_retries - 1:
                    logger.warning(f"Server error, retrying {attempt+1}")
                    time.sleep(retry_delay)
                    continue
                else:
                    status_code = 503 if "503" in error_msg else 500
                    detail = "Service temporarily unavailable" if status_code == 503 else "Internal server error"
                    raise HTTPException(status_code=status_code, detail=f"{detail}. Please try again later.")

            # If we've exhausted retries or it's another type of error
            if attempt >= max_retries - 1:
                # Use fallback response instead of throwing an error
                logger.warning(f"Using fallback response after {max_retries} failed attempts")
                fallback = get_fallback_response(user_message)
                return {"response": fallback}

            # Otherwise, retry
            time.sleep(retry_delay)
