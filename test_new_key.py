"""
Test the new OpenAI API key
"""
import openai

new_key = "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"

print("=" * 60)
print("Testing New OpenAI API Key...")
print("=" * 60)
print(f"Key (first 20 chars): {new_key[:20]}...")
print(f"Key (last 10 chars): ...{new_key[-10:]}")
print(f"Key length: {len(new_key)}")
print()

try:
    openai.api_key = new_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'API key is working!' in one sentence."}
        ],
        max_tokens=50
    )
    print("✅ NEW API KEY IS VALID AND WORKING!")
    print(f"Response: {response.choices[0].message.content}")
    print("\nThis key can be used in your .env file.")
except Exception as e:
    print("❌ NEW API KEY FAILED!")
    print(f"Error: {str(e)}")

print("=" * 60)
