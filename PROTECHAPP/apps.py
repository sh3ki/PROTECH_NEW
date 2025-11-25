from django.apps import AppConfig
import os


class ProtechappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'PROTECHAPP'
    
    def ready(self):
        """
        Initialize Firebase when Django starts
        """
        # Only run in the main process, not in the reloader process
        if os.environ.get('RUN_MAIN') == 'true':
            # Import here to avoid circular imports
            from PROTECH.firebase_config import initialize_firebase
            
            # Initialize Firebase once at startup
            initialize_firebase()
            print("✓ Firebase initialized at Django startup")

