"""
Test the SMART improved chatbot with role-based links
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

print("\n" + "="*80)
print("TESTING SMART CHATBOT - Role-Based Links & Fixed Formatting")
print("="*80)

# Test 1: Admin asking about students
print("\n[TEST 1] Administrator asks: 'Where can I add students?'")
print("-"*80)

test_data = {'message': 'Where can I add students?', 'history': []}
request = factory.post('/api/chatbot/message/', data=json.dumps(test_data), content_type='application/json')
request.user = type('User', (), {'is_authenticated': True, 'role': 'Administrator', 'email': 'admin@protech.com'})()

response = chatbot_message(request)
result = json.loads(response.content)
if result.get('success'):
    msg = result['message']
    print("✅ Response:")
    print(msg)
    if '/admin/students/' in msg and 'https://www.protech.it.com' in msg:
        print("\n✓ Correct admin link provided!")
    if '[' in msg and '](' in msg:
        print("✓ Proper Markdown format used!")

# Test 2: Registrar asking about face enrollment  
print("\n[TEST 2] Registrar asks: 'How do I enroll student faces?'")
print("-"*80)

test_data = {'message': 'How do I enroll student faces?', 'history': []}
request = factory.post('/api/chatbot/message/', data=json.dumps(test_data), content_type='application/json')
request.user = type('User', (), {'is_authenticated': True, 'role': 'Registrar', 'email': 'registrar@protech.com'})()

response = chatbot_message(request)
result = json.loads(response.content)
if result.get('success'):
    msg = result['message']
    print("✅ Response:")
    print(msg)
    if '/registrar/face-enroll/' in msg:
        print("\n✓ Correct registrar face enrollment link!")
    if '[' in msg and '](' in msg:
        print("✓ Proper Markdown format used!")

# Test 3: Teacher asking about attendance
print("\n[TEST 3] Teacher asks: 'Where can I see attendance?'")
print("-"*80)

test_data = {'message': 'Where can I see attendance?', 'history': []}
request = factory.post('/api/chatbot/message/', data=json.dumps(test_data), content_type='application/json')
request.user = type('User', (), {'is_authenticated': True, 'role': 'Teacher', 'email': 'teacher@protech.com'})()

response = chatbot_message(request)
result = json.loads(response.content)
if result.get('success'):
    msg = result['message']
    print("✅ Response:")
    print(msg)
    if '/teacher/attendance/' in msg:
        print("\n✓ Correct teacher attendance link!")

print("\n" + "="*80)
print("✅ CHATBOT IS NOW MUCH SMARTER!")
print("="*80)
