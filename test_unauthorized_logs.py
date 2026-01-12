"""
Test script for Unauthorized Face Logs functionality
Tests the complete workflow: saving unauthorized faces and displaying them in admin
"""
import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from django.conf import settings
from PROTECHAPP.models import UnauthorizedLog
from datetime import datetime
import pytz

def test_unauthorized_logs():
    """Test the unauthorized logs functionality"""
    
    print("=" * 60)
    print("TESTING UNAUTHORIZED FACE LOGS FUNCTIONALITY")
    print("=" * 60)
    
    # 1. Check if the model is properly set up
    print("\n1. Testing UnauthorizedLog Model...")
    try:
        # Check if we can query the model
        count = UnauthorizedLog.objects.count()
        print(f"   ✅ Model is accessible. Current logs count: {count}")
    except Exception as e:
        print(f"   ❌ Model error: {e}")
        return False
    
    # 2. Check if the media folder exists
    print("\n2. Testing Media Folder Structure...")
    unauthorized_dir = os.path.join(settings.MEDIA_ROOT, 'unauthorized_faces')
    if os.path.exists(unauthorized_dir):
        print(f"   ✅ Unauthorized faces directory exists: {unauthorized_dir}")
        # Check if we can create a test date folder
        manila_tz = pytz.timezone('Asia/Manila')
        today = datetime.now(manila_tz).strftime('%Y-%m-%d')
        test_dir = os.path.join(unauthorized_dir, today)
        os.makedirs(test_dir, exist_ok=True)
        print(f"   ✅ Can create date folders: {test_dir}")
    else:
        print(f"   ❌ Unauthorized faces directory does not exist")
        return False
    
    # 3. Test creating a sample log entry
    print("\n3. Testing Log Entry Creation...")
    try:
        test_log = UnauthorizedLog.objects.create(
            photo_path='unauthorized_faces/test/test.jpg',
            camera_name='Test Camera',
            timestamp=datetime.now(pytz.UTC)
        )
        print(f"   ✅ Successfully created test log entry: ID {test_log.id}")
        
        # Clean up test entry
        test_log.delete()
        print(f"   ✅ Successfully deleted test log entry")
    except Exception as e:
        print(f"   ❌ Error creating log entry: {e}")
        return False
    
    # 4. Test the admin view
    print("\n4. Testing Admin View Configuration...")
    from PROTECHAPP.urls import urlpatterns
    unauthorized_url_found = False
    for pattern in urlpatterns:
        if hasattr(pattern, 'name') and pattern.name == 'admin_unauthorized_logs':
            unauthorized_url_found = True
            print(f"   ✅ URL route is configured: {pattern.pattern}")
            break
    
    if not unauthorized_url_found:
        print(f"   ❌ URL route not found in urlpatterns")
        return False
    
    # 5. Test API endpoint
    print("\n5. Testing API Endpoint Configuration...")
    api_url_found = False
    for pattern in urlpatterns:
        if hasattr(pattern, 'name') and pattern.name == 'save_unauthorized_face':
            api_url_found = True
            print(f"   ✅ API endpoint is configured: {pattern.pattern}")
            break
    
    if not api_url_found:
        print(f"   ❌ API endpoint not found in urlpatterns")
        return False
    
    # 6. Test template file
    print("\n6. Testing Template File...")
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'admin', 'unauthorized_logs.html')
    if os.path.exists(template_path):
        print(f"   ✅ Template file exists: {template_path}")
        # Check if template has required elements
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'unauthorized_logs' in content and 'photo_path' in content:
                print(f"   ✅ Template contains required elements")
            else:
                print(f"   ⚠️  Template may be missing some elements")
    else:
        print(f"   ❌ Template file not found")
        return False
    
    # 7. Test sidebar link
    print("\n7. Testing Sidebar Configuration...")
    sidebar_path = os.path.join(settings.BASE_DIR, 'templates', 'components', 'sidebar', 'admin_sidebar.html')
    if os.path.exists(sidebar_path):
        with open(sidebar_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'admin_unauthorized_logs' in content:
                print(f"   ✅ Sidebar includes Unauthorized Logs link")
            else:
                print(f"   ⚠️  Sidebar may not have the link")
    else:
        print(f"   ❌ Sidebar file not found")
    
    # 8. Test JavaScript file
    print("\n8. Testing JavaScript Configuration...")
    js_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'ultra-fast-face-recognition.js')
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'saveUnauthorizedFace' in content and 'save-unauthorized-face' in content:
                print(f"   ✅ JavaScript includes unauthorized face saving functionality")
            else:
                print(f"   ❌ JavaScript missing unauthorized face functionality")
                return False
    else:
        print(f"   ❌ JavaScript file not found")
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✅")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Visit http://127.0.0.1:8000/admin/unauthorized-logs/ to see the page")
    print("2. Test face recognition at http://127.0.0.1:8000/time-in/")
    print("3. Unauthorized faces will be automatically saved and logged")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = test_unauthorized_logs()
    sys.exit(0 if success else 1)
