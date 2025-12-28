"""
Test the improved chatbot with link generation
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
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a test request
factory = RequestFactory()

# Test scenarios
test_cases = [
    {
        "scenario": "User NOT logged in - asks about login",
        "message": "Where can I login?",
        "authenticated": False
    },
    {
        "scenario": "User NOT logged in - asks about adding students",
        "message": "Where can I add students?",
        "authenticated": False
    },
    {
        "scenario": "User logged in as Admin - asks about adding students",
        "message": "Where can I add students?",
        "authenticated": True,
        "role": "Administrator"
    },
    {
        "scenario": "User logged in as Registrar - asks about face enrollment",
        "message": "Where can I enroll student faces?",
        "authenticated": True,
        "role": "Registrar"
    }
]

print("=" * 70)
print("TESTING IMPROVED CHATBOT WITH LINK GENERATION")
print("=" * 70)

for i, test_case in enumerate(test_cases, 1):
    print(f"\n{'='*70}")
    print(f"TEST {i}: {test_case['scenario']}")
    print(f"{'='*70}")
    print(f"Message: \"{test_case['message']}\"")
    print(f"Authenticated: {test_case.get('authenticated', False)}")
    if test_case.get('authenticated'):
        print(f"Role: {test_case.get('role', 'Unknown')}")
    print()
    
    # Create POST request
    test_data = {
        'message': test_case['message'],
        'history': []
    }
    
    request = factory.post(
        '/api/chatbot/message/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    # Mock authentication
    if test_case.get('authenticated'):
        # Create a mock user
        request.user = type('User', (), {
            'is_authenticated': True,
            'role': test_case.get('role', 'Administrator')
        })()
    else:
        request.user = type('AnonymousUser', (), {
            'is_authenticated': False
        })()
    
    # Call the view
    response = chatbot_message(request)
    
    # Parse response
    response_data = json.loads(response.content)
    
    print("RESPONSE:")
    print("-" * 70)
    if response_data.get('success'):
        print("✅ SUCCESS!")
        print()
        message = response_data.get('message')
        print(message)
        
        # Check if response contains links
        if 'https://www.protech.it.com' in message or 'https://protech.it.com' in message:
            print("\n✓ Response includes website links")
    else:
        print("❌ FAILED!")
        print(f"Error: {response_data.get('error')}")
    
    print()

print("=" * 70)
print("ALL TESTS COMPLETED")
print("=" * 70)
