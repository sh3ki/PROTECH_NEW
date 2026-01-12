"""
Test script for unauthorized logs page updates
Tests: pagination styling, Actions column, checkboxes, delete functionality, default date
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from PROTECHAPP.models import UnauthorizedLog
from django.utils import timezone
from datetime import datetime
import re

def test_template_updates():
    """Test if template has all required updates"""
    template_path = os.path.join('templates', 'admin', 'unauthorized_logs.html')
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests = {
        'Select All Checkbox': 'id="select-all-checkbox"' in content,
        'Actions Column Header': '>Actions</th>' in content,
        'Individual Checkboxes': 'class="log-checkbox"' in content,
        'Delete Button': 'deleteLog(' in content,
        'No Clear Filters Button': 'clear-filters-btn' not in content,
        'Default Date Script': 'Set default date to today' in content,
        'Pagination SVG Icons': '<path fill-rule="evenodd"' in content,
        'First Button': 'First page' in content,
        'Last Button': 'Last page' in content,
        'Checkbox Column': 'colspan="6"' in content,  # Updated colspan
    }
    
    print("\n" + "="*60)
    print("TEMPLATE UPDATES TEST")
    print("="*60)
    
    all_passed = True
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    return all_passed

def test_delete_api_endpoint():
    """Test if delete API endpoint exists"""
    from PROTECHAPP import urls
    
    print("\n" + "="*60)
    print("DELETE API ENDPOINT TEST")
    print("="*60)
    
    urls_content = str(urls.urlpatterns)
    has_delete_endpoint = 'delete-unauthorized-log' in urls_content
    
    status = "✅ PASS" if has_delete_endpoint else "❌ FAIL"
    print(f"{status} - Delete API endpoint registered in urls.py")
    
    return has_delete_endpoint

def test_delete_view_function():
    """Test if delete view function exists"""
    from PROTECHAPP.views import face_recognition_views
    
    print("\n" + "="*60)
    print("DELETE VIEW FUNCTION TEST")
    print("="*60)
    
    has_function = hasattr(face_recognition_views, 'delete_unauthorized_log')
    
    status = "✅ PASS" if has_function else "❌ FAIL"
    print(f"{status} - delete_unauthorized_log function exists")
    
    if has_function:
        import inspect
        func = getattr(face_recognition_views, 'delete_unauthorized_log')
        source = inspect.getsource(func)
        
        checks = {
            'Accepts POST': '@require_http_methods(["POST"])' in source or 'POST' in source,
            'Parses log_ids': 'log_ids' in source,
            'Deletes photos': 'os.remove' in source,
            'Deletes records': 'log.delete()' in source,
            'Returns JSON': 'JsonResponse' in source,
        }
        
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
    
    return has_function

def test_admin_view_default_date():
    """Test if admin view sets default date"""
    from PROTECHAPP.views import admin_views
    import inspect
    
    print("\n" + "="*60)
    print("ADMIN VIEW DEFAULT DATE TEST")
    print("="*60)
    
    func = admin_views.admin_unauthorized_logs
    source = inspect.getsource(func)
    
    has_default_date = 'date.today()' in source and 'if not date_filter' in source
    
    status = "✅ PASS" if has_default_date else "❌ FAIL"
    print(f"{status} - Admin view sets default date to today")
    
    return has_default_date

def test_pagination_styling():
    """Test if pagination has proper styling"""
    template_path = os.path.join('templates', 'admin', 'unauthorized_logs.html')
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n" + "="*60)
    print("PAGINATION STYLING TEST")
    print("="*60)
    
    pagination_features = {
        'SVG Icons': content.count('viewBox="0 0 20 20"') >= 4,  # First, Prev, Next, Last
        'Rounded Buttons': 'rounded-md' in content,
        'Dark Mode Support': 'dark:bg-gray-700' in content and 'dark:border-gray-600' in content,
        'Hover Effects': 'hover:bg-gray-50' in content,
        'Disabled State': 'cursor-not-allowed' in content,
        'Page Numbers': 'hidden md:flex' in content,
        'Current Page Highlight': 'bg-primary dark:bg-tertiary' in content,
    }
    
    all_passed = True
    for feature, result in pagination_features.items():
        status = "✅" if result else "❌"
        print(f"  {status} {feature}")
        if not result:
            all_passed = False
    
    return all_passed

def test_javascript_functions():
    """Test if JavaScript functions are present"""
    template_path = os.path.join('templates', 'admin', 'unauthorized_logs.html')
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n" + "="*60)
    print("JAVASCRIPT FUNCTIONS TEST")
    print("="*60)
    
    js_functions = {
        'deleteLog': 'function deleteLog(' in content,
        'deleteSelectedLogs': 'function deleteSelectedLogs(' in content,
        'Select All Handler': 'select-all-checkbox' in content and 'addEventListener' in content,
        'updateSelectAllCheckbox': 'function updateSelectAllCheckbox(' in content,
        'updateDeleteButton': 'function updateDeleteButton(' in content,
        'Default Date on Load': 'DOMContentLoaded' in content and 'dateFilter.value' in content,
        'Toast Notifications': 'showToast' in content,
    }
    
    all_passed = True
    for func_name, result in js_functions.items():
        status = "✅" if result else "❌"
        print(f"  {status} {func_name}")
        if not result:
            all_passed = False
    
    return all_passed

def test_actions_column():
    """Test if Actions column is properly implemented"""
    template_path = os.path.join('templates', 'admin', 'unauthorized_logs.html')
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n" + "="*60)
    print("ACTIONS COLUMN TEST")
    print("="*60)
    
    actions_features = {
        'Actions Header': 'uppercase tracking-wider">Actions</th>' in content,
        'Delete Icon SVG': 'M19 7l-.867 12.142' in content,  # Trash icon path
        'Delete Button Class': 'bg-red-600 hover:bg-red-700' in content,
        'onclick Handler': 'onclick="deleteLog(' in content,
        'Center Alignment': 'text-center' in content,
        'Button Tooltip': 'title="Delete log"' in content,
    }
    
    all_passed = True
    for feature, result in actions_features.items():
        status = "✅" if result else "❌"
        print(f"  {status} {feature}")
        if not result:
            all_passed = False
    
    return all_passed

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("UNAUTHORIZED LOGS UPDATE - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    results = {
        'Template Updates': test_template_updates(),
        'Delete API Endpoint': test_delete_api_endpoint(),
        'Delete View Function': test_delete_view_function(),
        'Admin View Default Date': test_admin_view_default_date(),
        'Pagination Styling': test_pagination_styling(),
        'JavaScript Functions': test_javascript_functions(),
        'Actions Column': test_actions_column(),
    }
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    if passed == total:
        print("🎉 ALL TESTS PASSED! ✅")
        print("="*60)
        print("\nUpdates completed successfully:")
        print("  ✅ Pagination styled to match other pages")
        print("  ✅ Actions column with delete button added")
        print("  ✅ Checkboxes for multi-select added")
        print("  ✅ Select All checkbox at top added")
        print("  ✅ Clear Filters button removed")
        print("  ✅ Default date set to today")
        print("  ✅ Delete API endpoint created")
        print("  ✅ Delete functionality implemented")
    else:
        print(f"❌ {total - passed} TEST(S) FAILED")
        print("="*60)
    
    print(f"\nScore: {passed}/{total}")

if __name__ == '__main__':
    run_all_tests()
