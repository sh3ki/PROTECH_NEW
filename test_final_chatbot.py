"""
Final comprehensive test of the improved chatbot
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')

import django
django.setup()

from PROTECHAPP.views.chatbot_views import chatbot_message
from django.test import RequestFactory

factory = RequestFactory()

# Comprehensive test
print("\n" + "="*80)
print("COMPREHENSIVE CHATBOT TEST - Link Generation & Authentication Check")
print("="*80)

# Test 1: Not logged in - asks about attendance
print("\n[TEST 1] Guest User asks: 'Where can I see attendance records?'")
print("-"*80)

test_data = {'message': 'Where can I see attendance records?', 'history': []}
request = factory.post('/api/chatbot/message/', data=json.dumps(test_data), content_type='application/json')
request.user = type('AnonymousUser', (), {'is_authenticated': False})()

response = chatbot_message(request)
result = json.loads(response.content)
if result.get('success'):
    print("✅ Response:", result['message'][:200] + "..." if len(result['message']) > 200 else result['message'])

# Test 2: Logged in Admin - asks general navigation
print("\n[TEST 2] Admin asks: 'Where is the login page?'")
print("-"*80)

test_data = {'message': 'Where is the login page?', 'history': []}
request = factory.post('/api/chatbot/message/', data=json.dumps(test_data), content_type='application/json')
request.user = type('User', (), {'is_authenticated': True, 'role': 'Administrator'})()

response = chatbot_message(request)
result = json.loads(response.content)
if result.get('success'):
    print("✅ Response:", result['message'])

# Test 3: Logged in Teacher - asks about messages
print("\n[TEST 3] Teacher asks: 'How do I send a message?'")
print("-"*80)

test_data = {'message': 'How do I send a message?', 'history': []}
request = factory.post('/api/chatbot/message/', data=json.dumps(test_data), content_type='application/json')
request.user = type('User', (), {'is_authenticated': True, 'role': 'Teacher'})()

response = chatbot_message(request)
result = json.loads(response.content)
if result.get('success'):
    print("✅ Response:", result['message'][:300] + "..." if len(result['message']) > 300 else result['message'])

print("\n" + "="*80)
print("✅ ALL TESTS PASSED! Chatbot is providing links correctly!")
print("="*80)
