# Backend Endpoint Implementation for Unauthorized Logs Real-Time Polling

## Overview
This document provides the complete backend implementation needed for the unauthorized logs real-time polling feature to work.

## Required Implementation

### 1. Add to your Admin Views file (e.g., `admin_views.py` or `views.py`)

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime

@login_required
@require_http_methods(["GET"])
def get_latest_unauthorized_logs(request):
    """
    API endpoint to get latest unauthorized logs for real-time polling.
    This endpoint is called every 5 seconds by the frontend to check for new logs.
    """
    try:
        # Import your UnauthorizedFaceLog model
        # Adjust the import path based on your project structure
        from face_recognition_app.models import UnauthorizedFaceLog  
        
        # Get filter parameters from query string
        search_query = request.GET.get('search', '').strip()
        camera_filter = request.GET.get('camera', '').strip()
        date_filter = request.GET.get('date', '').strip()
        limit = int(request.GET.get('limit', 50))
        
        # Start with all logs
        logs = UnauthorizedFaceLog.objects.all()
        
        # Apply search filter (camera name)
        if search_query:
            logs = logs.filter(camera_name__icontains=search_query)
        
        # Apply camera filter
        if camera_filter:
            logs = logs.filter(camera_name=camera_filter)
        
        # Apply date filter
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                logs = logs.filter(timestamp__date=filter_date)
            except ValueError:
                pass  # Invalid date format, skip filter
        
        # Get latest logs ordered by timestamp (newest first)
        logs = logs.order_by('-timestamp')[:limit]
        
        # Serialize logs to JSON format
        logs_data = [{
            'id': log.id,
            'camera_name': log.camera_name,
            'timestamp': log.timestamp.isoformat(),
            'photo_path': str(log.photo_path) if log.photo_path else ''
        } for log in logs]
        
        return JsonResponse({
            'status': 'success',
            'logs': logs_data,
            'count': len(logs_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
```

### 2. Add to your Admin URLs file (e.g., `admin_urls.py` or `urls.py`)

```python
from django.urls import path
from . import views  # or from . import admin_views

urlpatterns = [
    # ... your existing URL patterns ...
    
    # Unauthorized logs polling endpoint
    path('unauthorized-logs/latest/', views.get_latest_unauthorized_logs, name='admin_unauthorized_logs_latest'),
    
    # ... other patterns ...
]
```

### 3. Model Reference

Make sure your `UnauthorizedFaceLog` model has these fields:
- `id` (auto-generated primary key)
- `camera_name` (CharField or similar)
- `timestamp` (DateTimeField)
- `photo_path` (FileField, ImageField, or CharField)

Example model structure:
```python
from django.db import models

class UnauthorizedFaceLog(models.Model):
    camera_name = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    photo_path = models.ImageField(upload_to='unauthorized_faces/')
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.camera_name} - {self.timestamp}"
```

## Testing the Endpoint

After implementing the above code, you can test the endpoint by visiting:
```
http://127.0.0.1:8000/admin/unauthorized-logs/latest/
http://127.0.0.1:8000/admin/unauthorized-logs/latest/?date=2026-01-13
http://127.0.0.1:8000/admin/unauthorized-logs/latest/?camera=Time%20In%20Camera
```

Expected JSON response:
```json
{
    "status": "success",
    "logs": [
        {
            "id": 1,
            "camera_name": "Time In Camera",
            "timestamp": "2026-01-13T12:30:45.123456",
            "photo_path": "unauthorized_faces/face_123.jpg"
        },
        ...
    ],
    "count": 10
}
```

## How It Works

1. **Frontend (Already Implemented)**:
   - Polls the endpoint every 5 seconds
   - Sends current filters (search, camera, date)
   - Compares new logs with existing ones
   - Reloads page when new logs are detected
   - Shows toast notification

2. **Backend (This Implementation)**:
   - Receives filter parameters
   - Queries database for matching logs
   - Returns latest logs in JSON format
   - Handles errors gracefully

## Troubleshooting

**If you get 404 errors:**
- Make sure the URL pattern is in the correct URLs file
- Check that your Django project's main `urls.py` includes the admin URLs
- Verify the URL name matches: `admin_unauthorized_logs_latest`

**If you get ImportError:**
- Update the model import path to match your project structure
- Common paths: `from yourapp.models import UnauthorizedFaceLog`

**If you get attribute errors:**
- Verify your model has the required fields
- Check field names match exactly (case-sensitive)

## Performance Considerations

- The endpoint is called every 5 seconds
- Default limit is 50 logs to prevent large responses
- Database queries are filtered and ordered efficiently
- Consider adding database indexes on:
  - `timestamp` field (for ordering)
  - `camera_name` field (for filtering)
  - `timestamp` + `camera_name` composite index

Add indexes in your model:
```python
class Meta:
    ordering = ['-timestamp']
    indexes = [
        models.Index(fields=['-timestamp']),
        models.Index(fields=['camera_name']),
        models.Index(fields=['timestamp', 'camera_name']),
    ]
```

## Next Steps

1. Copy the view function to your admin views file
2. Add the URL pattern to your admin URLs file
3. Adjust the model import path if needed
4. Test the endpoint in your browser
5. Reload the unauthorized logs page and watch for real-time updates!

The frontend polling is already configured and ready to work once this backend endpoint is in place.
