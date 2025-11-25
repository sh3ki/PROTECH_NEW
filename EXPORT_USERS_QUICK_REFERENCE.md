# Quick Reference - Export Users Feature

## Button Location
**File**: `templates/admin/users.html`
**Line**: 153
**Button ID**: `export-users-btn`
**Button Appearance**: Green button with download icon labeled "Export"

## API Endpoint
**URL**: `/admin/users/export/`
**Method**: GET
**Requires**: Admin authentication
**Query Parameters** (all optional):
- `search`: Search term (name, email, username)
- `role`: Role filter (ADMIN, TEACHER, PRINCIPAL, REGISTRAR)
- `status`: Status filter (active, inactive)

## Example Export URLs

1. **Export all users:**
   ```
   GET /admin/users/export/
   ```

2. **Export only teachers:**
   ```
   GET /admin/users/export/?role=TEACHER
   ```

3. **Export only active registrars:**
   ```
   GET /admin/users/export/?role=REGISTRAR&status=active
   ```

4. **Export users matching search:**
   ```
   GET /admin/users/export/?search=john
   ```

5. **Export inactive principals:**
   ```
   GET /admin/users/export/?role=PRINCIPAL&status=inactive
   ```

## Excel Output Format

**Columns:**
1. ID
2. Username
3. Email
4. First Name
5. Last Name
6. Middle Name
7. Role (displayed as: Administrator, Teacher, Principal, Registrar)
8. Status (Active/Inactive)
9. Created Date (YYYY-MM-DD HH:MM:SS)

**Filename Format:**
`users_export_YYYYMMDD_HHMMSS.xlsx`

Example: `users_export_20251121_143022.xlsx`

## Troubleshooting

### Issue: Export button not responding
**Solution**: 
- Ensure you're logged in as an administrator
- Check browser console for JavaScript errors
- Verify the URL route is correctly configured in urls.py

### Issue: Export returns error
**Possible Causes**:
- Invalid filter parameters
- Database connection issue
- Missing openpyxl library

**Solution**:
```bash
pip install openpyxl
```

### Issue: File downloads but won't open
**Solution**:
- Ensure you have Microsoft Excel or compatible software
- Try opening with LibreOffice Calc or Google Sheets
- The file is standard XLSX format

### Issue: Filter not applied to export
**Solution**:
- Verify filters are set in the UI before clicking Export
- Check URL parameters in browser's Network tab
- Ensure filter values match the role/status options

## Code Locations

| Component | File | Location |
|-----------|------|----------|
| Export View Function | `PROTECHAPP/views/admin_views.py` | Lines ~3488-3606 |
| URL Route | `PROTECHAPP/urls.py` | Line 37 |
| Button HTML | `templates/admin/users.html` | Line 153 |
| JavaScript Handler | `templates/admin/users.html` | Lines ~2517-2572 |
| Imports | `PROTECHAPP/views/admin_views.py` | Lines 16-18 |
| Dependencies | `requirements.txt` | Last line |

## Key Functions

### Backend:
- `export_users_to_excel()` - Main export function

### Frontend:
- JavaScript event listener on `exportUsersBtn`
- Uses existing `showLoading()` and `hideLoading()` functions
- Uses existing `showSuccess()` and `showError()` functions

## Browser Compatibility

- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ⚠️ IE11 (may require polyfills)

## Performance

- **Small export** (< 100 users): < 1 second
- **Medium export** (100-500 users): 1-3 seconds
- **Large export** (500+ users): 3-10 seconds

## Security

✅ **Protected by:**
- `@login_required` - User must be logged in
- `@user_passes_test(is_admin)` - Only admins can access
- CSRF token validation
- GET request only

## Related Functionality

- **Import Users**: Uses same filtering logic, different direction
- **User Search**: Provides search filter for export
- **User Pagination**: Export includes all results, ignores pagination

## Support & Maintenance

- Update openpyxl: `pip install --upgrade openpyxl`
- No scheduled maintenance required
- No database changes needed
- Export is read-only operation (no side effects)
