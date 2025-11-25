"""
Test PhilSMS Integration
This script tests the PhilSMS API integration.
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from PROTECHAPP.philsms_service import PhilSMSService, send_sms
from django.conf import settings


def test_phone_formatting():
    """Test phone number formatting"""
    print("\n" + "="*60)
    print("TESTING PHONE NUMBER FORMATTING")
    print("="*60)
    
    service = PhilSMSService()
    
    test_cases = [
        "09171234567",
        "9171234567",
        "639171234567",
        "+639171234567",
        "09171234567 ",
        "0917-123-4567",
        "0917 123 4567",
    ]
    
    for phone in test_cases:
        formatted = service._format_phone_number(phone)
        print(f"Input: {phone:20} -> Output: {formatted}")
    
    print("\n✅ Phone number formatting test complete")


def test_api_connection():
    """Test API connection and configuration"""
    print("\n" + "="*60)
    print("TESTING API CONFIGURATION")
    print("="*60)
    
    api_token = settings.PHILSMS_API_TOKEN
    sender_id = getattr(settings, 'PHILSMS_SENDER_ID', 'Not configured')
    
    print(f"API Token: {api_token[:20]}...{api_token[-10:] if len(api_token) > 30 else api_token}")
    print(f"Sender ID: {sender_id}")
    
    if api_token:
        print("\n✅ API Token is configured")
    else:
        print("\n❌ API Token is NOT configured")
        return False
    
    return True


def send_test_sms():
    """Send a test SMS"""
    print("\n" + "="*60)
    print("SENDING TEST SMS")
    print("="*60)
    
    # Get phone number from user
    phone = input("\nEnter Philippine mobile number to test (e.g., 09171234567): ").strip()
    
    if not phone:
        print("❌ No phone number provided. Test cancelled.")
        return
    
    # Prepare test message
    message = """PROTECH Test SMS

This is a test message from PROTECH Attendance System.

If you receive this, the SMS integration is working correctly!

Date: November 24, 2025
Time: Testing Phase

-PROTECH System"""
    
    print(f"\nSending SMS to: {phone}")
    print(f"Message length: {len(message)} characters")
    print("\nMessage preview:")
    print("-" * 40)
    print(message)
    print("-" * 40)
    
    confirm = input("\nSend this SMS? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Test cancelled.")
        return
    
    print("\nSending SMS...")
    
    # Send SMS
    result = send_sms(
        phone_number=phone,
        message=message,
        sender_id=getattr(settings, 'PHILSMS_SENDER_ID', None)
    )
    
    print("\n" + "="*60)
    print("RESULT")
    print("="*60)
    
    if result['success']:
        print("✅ SMS sent successfully!")
        if 'data' in result:
            print(f"\nResponse data: {result['data']}")
    else:
        print("❌ SMS sending failed!")
        print(f"\nError: {result.get('error', 'Unknown error')}")
        if 'status_code' in result:
            print(f"Status Code: {result['status_code']}")
    
    print("\n" + "="*60)


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("PHILSMS INTEGRATION TEST")
    print("="*60)
    
    # Test 1: Phone formatting
    test_phone_formatting()
    
    # Test 2: API configuration
    if not test_api_connection():
        print("\n❌ Cannot proceed with SMS test - API not configured properly")
        return
    
    # Test 3: Send test SMS
    try:
        send_test_sms()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. If test SMS was successful, check your phone")
    print("2. Check PhilSMS dashboard for delivery status")
    print("3. Monitor your SMS credit balance")
    print("4. Test with actual student time-in via face recognition")
    print("\nSee PHILSMS_INTEGRATION_GUIDE.md for more information.")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
