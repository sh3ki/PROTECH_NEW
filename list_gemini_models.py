"""
List available Gemini models
"""
import google.generativeai as genai

gemini_key = "AIzaSyBbGOPfS-4jgIqrQB7hCPuFRdIj4nRd-7o"

print("=" * 60)
print("Listing Available Gemini Models...")
print("=" * 60)

try:
    genai.configure(api_key=gemini_key)
    
    print("\nAvailable models:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
    
    print("\n✅ API key is valid!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("=" * 60)
