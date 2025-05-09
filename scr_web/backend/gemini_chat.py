from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging
from typing import Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("Gemini API key not found in .env file")

# Configure Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Initialize model with safety settings
    model = genai.GenerativeModel('gemini-pro',
        generation_config={
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 2048,
        },
        safety_settings=[
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
    )
    logger.info("Gemini API initialized successfully with safety settings")
except Exception as e:
    logger.error(f"Failed to initialize Gemini API: {str(e)}")
    raise RuntimeError(f"Failed to initialize Gemini API: {str(e)}")

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_gemini(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        logger.info(f"Sending request to Gemini API: {req.message[:50]}...")
        
        # Generate response
        response = model.generate_content(
            req.message,
            safety_settings=[
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
        )
        
        if not response or not hasattr(response, 'text') or not response.text:
            logger.error("Empty or invalid response from Gemini API")
            raise HTTPException(status_code=500, detail="Invalid response from Gemini")
            
        logger.info("Successfully received response from Gemini API")
        return {"response": response.text}
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in chat_with_gemini: {error_msg}")
        
        if "400" in error_msg:
            raise HTTPException(status_code=400, detail="Invalid request")
        elif "429" in error_msg:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        elif "500" in error_msg:
            raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")
        elif "503" in error_msg:
            raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get response: {error_msg}")
