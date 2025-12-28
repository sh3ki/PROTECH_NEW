"""
Test the Gemini API key
"""
try:
    import google.generativeai as genai
    print("✅ google-generativeai library is installed")
except ImportError:
    print("❌ google-generativeai library is NOT installed")
    print("Installing it now...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'google-generativeai'])
    import google.generativeai as genai
    print("✅ google-generativeai library installed successfully")

gemini_key = "AIzaSyBbGOPfS-4jgIqrQB7hCPuFRdIj4nRd-7o"

print("\n" + "=" * 60)
print("Testing Gemini API Key...")
print("=" * 60)
print(f"Key (first 20 chars): {gemini_key[:20]}...")
print(f"Key (last 10 chars): ...{gemini_key[-10:]}")
print(f"Key length: {len(gemini_key)}")
print()

try:
    genai.configure(api_key=gemini_key)
    # Try gemini-1.5-flash first (latest model)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Gemini API is working!' in one sentence.")
    except:
        # Fallback to gemini-1.5-pro if flash fails
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("Say 'Gemini API is working!' in one sentence.")
    
    print("✅ GEMINI API KEY IS VALID AND WORKING!")
    print(f"Response: {response.text}")
    print("\nThis key can be used for the chatbot.")
except Exception as e:
    print("❌ GEMINI API KEY FAILED!")
    print(f"Error: {str(e)}")

print("=" * 60)
