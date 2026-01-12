# User Settings API Documentation

## Overview
Complete backend API for user settings management in PROTECH Face Recognition Attendance System.
All endpoints require authentication (user must be logged in).

## API Endpoints

### 1. Update Profile Picture
**Endpoint:** `/api/update-profile-picture/`  
**Method:** POST  
**Authentication:** Required  
**Content-Type:** multipart/form-data

**Request Body:**
- `profile_picture` (File): Image file (JPEG, PNG, GIF, or WebP)
  - Maximum size: 5MB
  - Recommended size: 400x400px
  - Automatically optimized and resized if needed

**Success Response (200):**
```json
{
  "success": true,
  "message": "Profile picture updated successfully",
  "profile_pic_url": "/media/profile_pics/user_1_1234567890.jpg"
}
```

**Error Responses:**
- 400: File size too large, invalid file type, or no file uploaded
- 500: Server error during upload

**Features:**
- Automatic image optimization (resized to max 800x800)
- RGBA to RGB conversion for compatibility
- Old profile picture automatically deleted
- Unique filename generation based on user ID and timestamp

---

### 2. Remove Profile Picture
**Endpoint:** `/api/remove-profile-picture/`  
**Method:** POST  
**Authentication:** Required  
**Content-Type:** application/json

**Request Body:** Empty (or CSRF token)

**Success Response (200):**
```json
{
  "success": true,
  "message": "Profile picture removed successfully"
}
```

**Error Response:**
- 500: Server error during deletion

**Features:**
- Deletes profile picture file from server
- Reverts to default avatar (user initials)
- Safe deletion with error handling

---

### 3. Update Profile Information
**Endpoint:** `/api/update-profile/`  
**Method:** POST  
**Authentication:** Required  
**Content-Type:** application/json

**Request Body:**
```json
{
  "first_name": "John",
  "middle_name": "Doe",
  "last_name": "Smith",
  "username": "john.smith",
  "email": "john.smith@example.com"
}
```

**Validation Rules:**
- `first_name`, `last_name`, `username`, `email` are required
- `middle_name` is optional
- Email must be valid format
- Username must be unique
- Email must be unique (case-insensitive)

**Success Response (200):**
```json
{
  "success": true,
  "message": "Profile updated successfully"
}
```

**Error Responses:**
- 400: Validation error (missing fields, invalid email, username/email taken)
- 500: Server error

**Features:**
- Real-time uniqueness checking for username and email
- Case-insensitive email comparison
- Whitespace trimming
- Email format validation using regex

---

### 4. Change Password
**Endpoint:** `/api/change-password/`  
**Method:** POST  
**Authentication:** Required  
**Content-Type:** application/json

**Request Body:**
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword456!",
  "confirm_password": "NewPassword456!"
}
```

**Validation Rules:**
- All fields required
- Current password must be correct
- New password minimum 8 characters
- New and confirm passwords must match
- New password must be different from current

**Success Response (200):**
```json
{
  "success": true,
  "message": "Password updated successfully"
}
```

**Error Responses:**
- 400: Validation error (wrong current password, passwords don't match, too short)
- 500: Server error

**Features:**
- Current password verification using Django authentication
- Automatic session preservation (user stays logged in)
- Password hashing using Django's security system
- Marks user as no longer "new" after first password change
- Prevents reusing current password

---

### 5. Delete Account
**Endpoint:** `/api/delete-account/`  
**Method:** POST  
**Authentication:** Required  
**Content-Type:** application/json

**Request Body:** Empty (username confirmation handled in frontend)

**Success Response (200):**
```json
{
  "success": true,
  "message": "Account deleted successfully"
}
```

**Error Response:**
- 500: Server error during deletion

**Features:**
- Atomic transaction ensures complete deletion or rollback
- Automatically deletes profile picture file
- Logs deletion for audit trail (user ID and username)
- Related records handled by database CASCADE/SET_NULL rules
- Irreversible action

---

## Security Features

### Authentication
- All endpoints require `@login_required` decorator
- Uses Django session-based authentication
- CSRF protection enabled on all POST requests

### Authorization
- Users can only modify their own account
- Uses `request.user` to ensure proper authorization
- No privilege escalation possible

### Data Validation
- Input sanitization (whitespace trimming)
- Email format validation
- File type and size validation
- Username/email uniqueness checks
- Password strength enforcement (minimum 8 characters)

### File Security
- Restricted file types (images only)
- File size limits (5MB maximum)
- Unique filename generation prevents overwriting
- Automatic cleanup of old files
- Image optimization reduces attack surface

### Error Handling
- Try-except blocks on all operations
- Detailed logging for debugging
- Generic error messages to users (security through obscurity)
- Transaction rollback on failures

---

## Frontend Integration

### CSRF Token
All POST requests must include Django's CSRF token:
```javascript
headers: {
  'X-CSRFToken': getCookie('csrftoken')
}
```

### Success/Error Handling
```javascript
const response = await fetch('/api/endpoint/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken')
  },
  body: JSON.stringify(data)
});

const result = await response.json();
if (response.ok && result.success) {
  // Handle success
  showToast(result.message, 'success');
} else {
  // Handle error
  showToast(result.message, 'error');
}
```

### Profile Picture Upload
Use FormData for file uploads:
```javascript
const formData = new FormData();
formData.append('profile_picture', file);
formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

const response = await fetch('/api/update-profile-picture/', {
  method: 'POST',
  body: formData  // Don't set Content-Type header for FormData
});
```

---

## Database Schema

### CustomUser Model Fields Used
```python
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    profile_pic = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=20, choices=UserRole.choices)
    is_new = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Inherited from AbstractUser:
    # - username, first_name, last_name
    # - password (hashed)
    # - last_login, date_joined
```

---

## File Storage

### Profile Pictures
- **Location:** `MEDIA_ROOT/profile_pics/`
- **Naming:** `user_{user_id}_{timestamp}.{extension}`
- **Accessible at:** `/media/profile_pics/{filename}`
- **Automatic cleanup:** Old pictures deleted on update/removal

### Storage Settings (settings.py)
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

---

## Testing

### Manual Testing with cURL

1. **Update Profile:**
```bash
curl -X POST http://localhost:8000/api/update-profile/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{"first_name":"John","middle_name":"","last_name":"Doe","username":"jdoe","email":"jdoe@example.com"}'
```

2. **Change Password:**
```bash
curl -X POST http://localhost:8000/api/change-password/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{"current_password":"oldpass","new_password":"newpass123","confirm_password":"newpass123"}'
```

3. **Upload Profile Picture:**
```bash
curl -X POST http://localhost:8000/api/update-profile-picture/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -F "csrfmiddlewaretoken=YOUR_CSRF_TOKEN" \
  -F "profile_picture=@/path/to/image.jpg"
```

---

## Error Codes

| HTTP Status | Meaning |
|-------------|---------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (not logged in) |
| 500 | Internal Server Error |

---

## Logging

All operations are logged with appropriate levels:
- **INFO:** Successful operations
- **WARNING:** Minor issues (e.g., file deletion failures)
- **ERROR:** Major errors requiring attention

Log format:
```
INFO 2026-01-12 10:30:45 user_settings_views Profile updated for user john.smith
WARNING 2026-01-12 10:31:15 user_settings_views Could not delete old profile picture: [Errno 2] No such file or directory
ERROR 2026-01-12 10:32:00 user_settings_views Error updating profile: ValidationError
```

---

## Deployment Checklist

- [ ] Ensure `MEDIA_ROOT` directory exists and is writable
- [ ] Configure web server to serve `/media/` files
- [ ] Set up backup for profile pictures
- [ ] Configure proper file permissions (755 for directories, 644 for files)
- [ ] Enable HTTPS for secure password transmission
- [ ] Set up log rotation for application logs
- [ ] Test with real user accounts
- [ ] Verify CSRF protection is enabled
- [ ] Check email validation works with your domain

---

## Troubleshooting

### Profile Picture Upload Fails
1. Check `MEDIA_ROOT` directory permissions
2. Verify disk space available
3. Check file size limits in web server config
4. Ensure PIL/Pillow is installed: `pip install Pillow`

### Username/Email Already Exists Errors
1. Database uniqueness constraints are enforced
2. Check for case-sensitivity issues
3. Verify email comparison is case-insensitive

### Password Change Doesn't Work
1. Verify current password is correct
2. Check password validation settings in Django
3. Ensure session middleware is properly configured

### Account Deletion Fails
1. Check database CASCADE rules
2. Verify user has permission to delete
3. Check for foreign key constraints
4. Review transaction logs

---

## Future Enhancements

- [ ] Two-factor authentication
- [ ] Email verification for email changes
- [ ] Password strength meter on backend
- [ ] Account deactivation (soft delete) option
- [ ] Export user data before deletion
- [ ] Profile picture cropping interface
- [ ] Activity log for security events
- [ ] Rate limiting on sensitive operations
