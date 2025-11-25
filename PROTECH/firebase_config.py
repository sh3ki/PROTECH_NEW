"""
Firebase Configuration and Initialization
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from django.conf import settings

# Initialize Firebase
_firebase_initialized = False
_db = None

def initialize_firebase():
    """
    Initialize Firebase Admin SDK
    """
    global _firebase_initialized, _db
    
    # If already initialized and db client exists, return it
    if _firebase_initialized and _db is not None:
        return _db
    
    try:
        # Check if Firebase app already exists
        try:
            app = firebase_admin.get_app()
            # App exists, just get the client
            if _db is None:
                _db = firestore.client()
            _firebase_initialized = True
            return _db
        except ValueError:
            # App doesn't exist yet, need to initialize
            pass
        
        # Path to your Firebase service account key JSON file
        cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _db = firestore.client()
            _firebase_initialized = True
            print("Firebase initialized successfully")
        else:
            print(f"Firebase credentials not found at: {cred_path}")
            print("Please configure FIREBASE_CREDENTIALS_PATH in settings.py")
            _db = None
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        _db = None
    
    return _db

def get_firestore_client():
    """
    Get Firestore client instance
    """
    global _db
    
    if not _firebase_initialized:
        return initialize_firebase()
    
    return _db

def is_firebase_configured():
    """
    Check if Firebase is properly configured
    Returns True if Firebase is initialized and ready to use
    """
    global _firebase_initialized, _db
    
    # If not initialized, try to initialize
    if not _firebase_initialized or _db is None:
        initialize_firebase()
    
    return _firebase_initialized and _db is not None
