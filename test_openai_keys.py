"""
Test script to verify OpenAI API keys
"""
import openai
from decouple import config

# Test Primary Key
print("=" * 60)
print("Testing Primary OpenAI API Key...")
print("=" * 60)

primary_key = config('OPENAI_API_KEY', default='')
print(f"Primary Key (first 20 chars): {primary_key[:20]}...")
print(f"Primary Key (last 10 chars): ...{primary_key[-10:]}")
print(f"Primary Key length: {len(primary_key)}")

try:
    openai.api_key = primary_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'Primary key works!'"}
        ],
        max_tokens=20
    )
    print("✅ PRIMARY KEY IS VALID!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print("❌ PRIMARY KEY FAILED!")
    print(f"Error: {str(e)}")

print("\n")

# Test Fallback Key
print("=" * 60)
print("Testing Fallback OpenAI API Key...")
print("=" * 60)

fallback_key = config('OPENAI_API_KEY_FALLBACK', default='')
print(f"Fallback Key (first 20 chars): {fallback_key[:20]}...")
print(f"Fallback Key (last 10 chars): ...{fallback_key[-10:]}")
print(f"Fallback Key length: {len(fallback_key)}")

try:
    openai.api_key = fallback_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'Fallback key works!'"}
        ],
        max_tokens=20
    )
    print("✅ FALLBACK KEY IS VALID!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print("❌ FALLBACK KEY FAILED!")
    print(f"Error: {str(e)}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
