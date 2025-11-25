"""
Simple test script to verify PROTECH AI Chatbot setup
Run this to test if OpenAI integration is working
"""

import os
import sys
from decouple import config

# Test environment variables
print("=" * 60)
print("PROTECH AI Chatbot - Configuration Test")
print("=" * 60)

# Check OpenAI API keys
openai_key = config('OPENAI_API_KEY', default='')
openai_key_fallback = config('OPENAI_API_KEY_FALLBACK', default='')

print("\n1. Environment Variables:")
print(f"   ✓ OPENAI_API_KEY: {'Set' if openai_key else '✗ NOT SET'}")
if openai_key:
    print(f"     (Key starts with: {openai_key[:20]}...)")
    
print(f"   ✓ OPENAI_API_KEY_FALLBACK: {'Set' if openai_key_fallback else '✗ NOT SET'}")
if openai_key_fallback:
    print(f"     (Key starts with: {openai_key_fallback[:20]}...)")

# Test OpenAI import
print("\n2. Package Installation:")
try:
    import openai
    print(f"   ✓ openai package installed (version {openai.__version__})")
except ImportError as e:
    print(f"   ✗ openai package not found: {e}")
    sys.exit(1)

# Test API connection (optional - requires valid API key)
print("\n3. API Connection Test:")
if openai_key:
    try:
        openai.api_key = openai_key
        print("   Testing API connection...")
        
        # Simple test call
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, PROTECH!' in one line."}
            ],
            max_tokens=20
        )
        
        print(f"   ✓ API connection successful!")
        print(f"   Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"   ✗ API connection failed: {e}")
        print("\n   Trying fallback key...")
        
        if openai_key_fallback:
            try:
                openai.api_key = openai_key_fallback
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say 'Hello, PROTECH!' in one line."}
                    ],
                    max_tokens=20
                )
                
                print(f"   ✓ Fallback API connection successful!")
                print(f"   Response: {response.choices[0].message.content}")
            except Exception as e2:
                print(f"   ✗ Fallback API also failed: {e2}")
else:
    print("   ⚠ Skipping API test (no API key configured)")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
print("\nIf all tests pass, the chatbot should work correctly.")
print("If API tests fail, check:")
print("  - API key validity")
print("  - OpenAI account status and billing")
print("  - Internet connection")
print("  - API rate limits")
