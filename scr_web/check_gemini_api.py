#!/usr/bin/env python3
"""
Script to check if the Gemini API key is valid and working.
This helps diagnose issues with the Gemini API integration.
"""

import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_api_key():
    """Check if the Gemini API key is valid and working"""
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("No Gemini API key found in .env file")
        print("\n❌ ERROR: No Gemini API key found in .env file")
        print("Please add your Gemini API key to the .env file:")
        print("GEMINI_API_KEY=your-api-key-here")
        return False
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # List available models
        print("\n🔍 Checking available Gemini models...")
        models = genai.list_models()
        model_names = [model.name for model in models]
        
        print(f"\nAvailable models ({len(model_names)}):")
        for name in model_names:
            print(f"  - {name}")
        
        # Check for specific models
        gemini_models = [name for name in model_names if "gemini" in name.lower()]
        if not gemini_models:
            logger.warning("No Gemini models found")
            print("\n⚠️ WARNING: No Gemini models found in the available models list")
            return False
        
        # Try to use a model
        print("\n🔍 Testing API with a simple query...")
        
        # Choose the best available model
        if "models/gemini-1.5-pro" in model_names:
            model_name = "gemini-1.5-pro"
        elif "models/gemini-1.0-pro" in model_names:
            model_name = "gemini-1.0-pro"
        else:
            model_name = "gemini-pro"  # Fallback to original name
        
        print(f"Using model: {model_name}")
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, are you working?")
        
        if response and hasattr(response, 'text'):
            print(f"\n✅ SUCCESS: API is working! Response: {response.text[:100]}...")
            return True
        else:
            logger.error("API returned an invalid response")
            print("\n❌ ERROR: API returned an invalid response")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Gemini API: {str(e)}")
        print(f"\n❌ ERROR: {str(e)}")
        
        if "404" in str(e) and "models/" in str(e):
            print("\nThe model name might be incorrect or not available for your API key.")
            print("Try updating to the latest version of the google-generativeai package:")
            print("pip install --upgrade google-generativeai")
        elif "403" in str(e):
            print("\nYour API key might be invalid or has insufficient permissions.")
            print("Get a new API key from: https://makersuite.google.com/app/apikey")
        
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Gemini API Key Checker")
    print("=" * 60)
    
    success = check_api_key()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Your Gemini API key is valid and working!")
        print("The chat functionality should work correctly.")
    else:
        print("❌ There are issues with your Gemini API key or configuration.")
        print("Please fix the issues mentioned above to enable chat functionality.")
        print("\nTo get a new API key:")
        print("1. Go to https://makersuite.google.com/app/apikey")
        print("2. Create a new API key")
        print("3. Add it to your .env file as GEMINI_API_KEY=your-new-key")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
