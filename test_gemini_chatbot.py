"""
Test the updated Gemini-based chatbot
"""
import json
import sys
import os

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')

import django
django.setup()

from PROTECHAPP.views.chatbot_views import chatbot_message
from django.test import RequestFactory

# Create a test request
factory = RequestFactory()

# Test message
test_data = {
    'message': 'Hello! How do I enroll a student?',
    'history': []
}

print("=" * 60)
print("Testing Gemini-Based Chatbot")
print("=" * 60)
print(f"Test message: {test_data['message']}")
print()

# Create POST request
request = factory.post(
    '/api/chatbot/message/',
    data=json.dumps(test_data),
    content_type='application/json'
)

# Call the view
response = chatbot_message(request)

# Parse response
response_data = json.loads(response.content)

print("Response:")
print("-" * 60)
if response_data.get('success'):
    print("✅ SUCCESS!")
    print()
    print(f"Message: {response_data.get('message')}")
    print()
    print(f"Timestamp: {response_data.get('timestamp')}")
else:
    print("❌ FAILED!")
    print(f"Error: {response_data.get('error')}")

print("=" * 60)
