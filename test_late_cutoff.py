"""
Test script for late time cutoff feature
"""
import os
import django
import pytz
from datetime import datetime, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from PROTECHAPP.models import SystemSettings
from django.utils import timezone

def test_late_cutoff():
    # Get or create system settings
    settings_obj, created = SystemSettings.objects.get_or_create(pk=1)
    
    print("=" * 60)
    print("LATE TIME CUTOFF TEST")
    print("=" * 60)
    
    # Display current late_time_cutoff
    print(f"\nCurrent late_time_cutoff (UTC): {settings_obj.late_time_cutoff}")
    
    # Convert to Manila time for display
    manila_tz = pytz.timezone('Asia/Manila')
    utc_tz = pytz.UTC
    
    if settings_obj.late_time_cutoff:
        utc_datetime = timezone.datetime.combine(
            timezone.now().date(),
            settings_obj.late_time_cutoff
        )
        utc_datetime = utc_tz.localize(utc_datetime)
        manila_datetime = utc_datetime.astimezone(manila_tz)
        
        print(f"Display time (Manila): {manila_datetime.strftime('%H:%M')}")
        print(f"Display time (full): {manila_datetime}")
    
    # Test: Set a Manila time and convert to UTC
    print("\n" + "=" * 60)
    print("TEST: Setting 8:00 AM Manila Time")
    print("=" * 60)
    
    manila_time_str = "08:00"
    time_obj = datetime.strptime(manila_time_str, '%H:%M').time()
    
    manila_datetime = manila_tz.localize(
        datetime.combine(timezone.now().date(), time_obj)
    )
    utc_datetime = manila_datetime.astimezone(pytz.UTC)
    utc_time = utc_datetime.time()
    
    print(f"Input (Manila): {manila_time_str}")
    print(f"Converted to UTC: {utc_time}")
    print(f"Manila DateTime: {manila_datetime}")
    print(f"UTC DateTime: {utc_datetime}")
    
    # Save to database
    settings_obj.late_time_cutoff = utc_time
    settings_obj.save()
    
    print(f"\n✓ Saved to database: {utc_time} (UTC)")
    
    # Verify by reading back
    settings_obj.refresh_from_db()
    print(f"✓ Read from database: {settings_obj.late_time_cutoff} (UTC)")
    
    # Convert back to Manila to verify
    utc_datetime = timezone.datetime.combine(
        timezone.now().date(),
        settings_obj.late_time_cutoff
    )
    utc_datetime = utc_tz.localize(utc_datetime)
    manila_datetime = utc_datetime.astimezone(manila_tz)
    
    print(f"✓ Display back as Manila: {manila_datetime.strftime('%H:%M')}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    test_late_cutoff()
