"""
Quick script to check available Gemini models
"""
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    print("🔍 Checking available Gemini models...")
    try:
        # List available models
        models = genai.list_models()
        print("\n✅ Available models:")
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"- {model.name}")
                print(f"  Display name: {model.display_name}")
                print(f"  Description: {model.description}")
                print()
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No Gemini API key found")