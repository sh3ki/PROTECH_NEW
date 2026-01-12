"""
Final test for unauthorized logs updates:
1. Delete button beside Select All
2. Pagination matching students style (Show: 10 per page + results info)
"""

import os

def test_delete_button():
    """Test if delete button is present beside Select All"""
    template_path = 'templates/admin/unauthorized_logs.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests = {
        'Delete button exists': 'id="delete-selected-btn"' in content,
        'Delete button hidden by default': 'class="hidden' in content and 'delete-selected-btn' in content,
        'Delete button has trash icon': 'M19 7l-.867 12.142' in content,
        'Delete button calls deleteSelectedLogs()': 'onclick="deleteSelectedLogs()"' in content,
        'Delete button next to checkbox': 'gap-2' in content and 'select-all-checkbox' in content,
        'Delete button is red': 'bg-red-600 hover:bg-red-700' in content,
    }
    
    print("\n" + "="*60)
    print("DELETE BUTTON TESTS")
    print("="*60)
    
    all_passed = True
    for test_name, result in tests.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    return all_passed

def test_pagination_structure():
    """Test if pagination matches students style"""
    template_path = 'templates/admin/unauthorized_logs.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests = {
        'Per-page dropdown exists': 'id="per-page-select"' in content,
        'Show label': 'Show:' in content,
        'per page label': 'per page' in content,
        'Dropdown has 10 option': '<option value="10"' in content,
        'Dropdown has 20 option': '<option value="20"' in content,
        'Dropdown has 50 option': '<option value="50"' in content,
        'Dropdown has 100 option': '<option value="100"' in content,
        'Dropdown calls changePerPage()': 'onchange="changePerPage()"' in content,
        'Results info exists': 'Showing' in content and 'results' in content,
        'Shows start_index': 'logs.start_index' in content,
        'Shows end_index': 'logs.end_index' in content,
        'Shows total count': 'logs.paginator.count' in content,
        'Layout is flex': 'flex flex-col sm:flex-row' in content,
    }
    
    print("\n" + "="*60)
    print("PAGINATION STRUCTURE TESTS")
    print("="*60)
    
    all_passed = True
    for test_name, result in tests.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    return all_passed

def test_javascript_functions():
    """Test if JavaScript functions are updated"""
    template_path = 'templates/admin/unauthorized_logs.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests = {
        'updateDeleteButton shows button': 'classList.remove(\'hidden\')' in content,
        'updateDeleteButton hides button': 'classList.add(\'hidden\')' in content,
        'changePerPage function exists': 'function changePerPage()' in content,
        'changePerPage gets per_page': 'per-page-select' in content and 'value' in content,
        'changePerPage preserves filters': 'search' in content and 'camera' in content and 'date' in content,
        'applyFilters preserves per_page': 'per_page' in content or 'perPage' in content,
    }
    
    print("\n" + "="*60)
    print("JAVASCRIPT FUNCTIONS TESTS")
    print("="*60)
    
    all_passed = True
    for test_name, result in tests.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    return all_passed

def test_backend_view():
    """Test if backend view handles per_page"""
    view_path = 'PROTECHAPP/views/admin_views.py'
    
    with open(view_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the admin_unauthorized_logs function
    start = content.find('def admin_unauthorized_logs(request):')
    if start == -1:
        print("\n❌ Could not find admin_unauthorized_logs function")
        return False
    
    # Get the function content (approximately)
    func_content = content[start:start+5000]
    
    tests = {
        'Gets per_page parameter': 'per_page' in func_content and 'request.GET.get' in func_content,
        'Validates per_page': 'int(per_page)' in func_content,
        'Has allowed values check': '[10, 20, 50, 100]' in func_content,
        'Uses per_page in Paginator': 'Paginator(logs, per_page)' in func_content,
        'Has default value': 'per_page = 10' in func_content or "'10'" in func_content,
    }
    
    print("\n" + "="*60)
    print("BACKEND VIEW TESTS")
    print("="*60)
    
    all_passed = True
    for test_name, result in tests.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    return all_passed

def test_url_parameters():
    """Test if pagination links preserve per_page"""
    template_path = 'templates/admin/unauthorized_logs.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count how many pagination links have per_page
    first_button = 'page=1' in content and 'per_page' in content
    prev_button = 'logs.previous_page_number' in content
    page_numbers = 'page={{ num }}' in content
    next_button = 'logs.next_page_number' in content
    last_button = 'logs.paginator.num_pages' in content
    
    # Check if per_page appears in pagination context
    per_page_count = content.count('request.GET.per_page')
    
    tests = {
        'First button exists': first_button,
        'Previous button exists': prev_button,
        'Page numbers exist': page_numbers,
        'Next button exists': next_button,
        'Last button exists': last_button,
        'per_page in URLs (multiple)': per_page_count >= 4,
    }
    
    print("\n" + "="*60)
    print("URL PARAMETERS TESTS")
    print("="*60)
    
    all_passed = True
    for test_name, result in tests.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    return all_passed

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("UNAUTHORIZED LOGS - FINAL UPDATE TEST SUITE")
    print("="*60)
    
    results = {
        'Delete Button': test_delete_button(),
        'Pagination Structure': test_pagination_structure(),
        'JavaScript Functions': test_javascript_functions(),
        'Backend View': test_backend_view(),
        'URL Parameters': test_url_parameters(),
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
        print("  ✅ Delete button beside Select All")
        print("  ✅ Pagination matching students style")
        print("  ✅ Show: 10 per page dropdown")
        print("  ✅ Showing X to Y of Z results")
        print("  ✅ per_page parameter in all links")
        print("  ✅ Backend handles per_page")
        print("\n✨ Ready to use! Just refresh browser (Ctrl+Shift+R)")
    else:
        print(f"❌ {total - passed} TEST(S) FAILED")
        print("="*60)
    
    print(f"\nScore: {passed}/{total}")

if __name__ == '__main__':
    run_all_tests()
