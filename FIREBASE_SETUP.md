# Firebase Firestore Setup Guide for PROTECH Messaging

This guide will walk you through setting up Firebase Firestore for the real-time messaging feature in your PROTECH application.

## Prerequisites

- A Google account
- Your PROTECH Django application running

## Step 1: Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or "Create a project"
3. Enter your project name (e.g., "PROTECH-Messaging")
4. Follow the setup wizard:
   - Enable/disable Google Analytics (optional)
   - Accept terms and click "Create project"
5. Wait for the project to be created

## Step 2: Enable Firestore Database

1. In your Firebase project, click on "Firestore Database" in the left sidebar
2. Click "Create database"
3. Choose a starting mode:
   - **Production mode** (recommended for production)
   - **Test mode** (for development - allows read/write access for 30 days)
4. Select a Firestore location (choose closest to your users)
5. Click "Enable"

## Step 3: Set Up Firestore Security Rules

1. Go to "Firestore Database" > "Rules" tab
2. Replace the default rules with these (for production):

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Messages collection
    match /messages/{messageId} {
      // Users can read messages where they are sender or recipient
      allow read: if request.auth != null && 
                     (resource.data.sender_id == request.auth.uid || 
                      resource.data.recipient_id == request.auth.uid);
      
      // Users can create messages where they are the sender
      allow create: if request.auth != null && 
                       request.resource.data.sender_id == request.auth.uid;
      
      // Users can update messages if they are the recipient (for marking as read)
      allow update: if request.auth != null && 
                       resource.data.recipient_id == request.auth.uid;
      
      // No one can delete messages (optional - remove if you want deletion)
      allow delete: if false;
    }
  }
}
```

**Note:** For development/testing, you can use relaxed rules temporarily:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

⚠️ **Warning:** The relaxed rules above are NOT secure and should only be used during development!

3. Click "Publish"

## Step 4: Create a Service Account

1. In Firebase Console, click the gear icon (⚙️) next to "Project Overview"
2. Click "Project settings"
3. Go to the "Service accounts" tab
4. Click "Generate new private key"
5. Click "Generate key" in the popup
6. A JSON file will be downloaded - **keep this file secure!**

## Step 5: Configure Your Django Application

1. **Move the Service Account Key:**
   - Rename the downloaded JSON file to `firebase-credentials.json`
   - Move it to your project root directory:
     ```
     C:\Users\USER\Documents\SYSTEMS\WEB\PYTHON\DJANGO\PROTECH_NEW\firebase-credentials.json
     ```

2. **Add to .gitignore:**
   Create or update your `.gitignore` file to prevent committing the credentials:
   ```
   firebase-credentials.json
   *.json
   ```

3. **Update your `.env` file** (optional - if you want to use environment variables):
   ```
   FIREBASE_CREDENTIALS_PATH=C:\Users\USER\Documents\SYSTEMS\WEB\PYTHON\DJANGO\PROTECH_NEW\firebase-credentials.json
   ```

## Step 6: Install Python Dependencies

Run the following command in your terminal:

```powershell
pip install -r requirements.txt
```

This will install:
- `firebase-admin>=6.2.0`
- `google-cloud-firestore>=2.13.0`

## Step 7: Initialize Firebase in Your Application

The Firebase initialization happens automatically when you start your Django application. The configuration is in:
- `PROTECH/firebase_config.py`

To verify it's working, you can check the console output when starting your Django server:

```powershell
python manage.py runserver
```

Look for: `Firebase initialized successfully`

## Step 8: Test the Messaging Feature

1. **Start your Django server:**
   ```powershell
   python manage.py runserver
   ```

2. **Login to your application** with two different accounts (in different browsers or incognito mode)

3. **Navigate to the Messages page:**
   - Admin: `http://127.0.0.1:8000/admin/messages/`
   - Principal: `http://127.0.0.1:8000/principal/messages/`
   - Registrar: `http://127.0.0.1:8000/registrar/messages/`

4. **Test the features:**
   - Click "New Message" to start a conversation
   - Search for a user
   - Send messages
   - Check real-time updates (messages should appear without refreshing)

## Firestore Database Structure

The messages are stored in Firestore with this structure:

### Collection: `messages`

Each document contains:
```javascript
{
  conversation_id: "123_456",           // Sorted user IDs concatenated
  sender_id: "123",                     // User ID of sender
  sender_name: "John Doe",              // Full name of sender
  sender_role: "admin",                 // Role of sender
  recipient_id: "456",                  // User ID of recipient
  recipient_name: "Jane Smith",         // Full name of recipient
  recipient_role: "teacher",            // Role of recipient
  message: "Hello, how are you?",       // Message content
  timestamp: Timestamp(2025-11-22...),  // Firebase timestamp
  read: false                           // Read status
}
```

## Firestore Indexes

Firebase will automatically create the necessary indexes when you run queries. If you encounter index errors:

1. The error message will contain a URL
2. Click the URL to automatically create the required index
3. Wait for the index to build (usually 1-2 minutes)

Common indexes needed:
- **Collection:** `messages`
  - Fields: `sender_id` (Ascending), `timestamp` (Descending)
  - Fields: `recipient_id` (Ascending), `timestamp` (Descending)
  - Fields: `conversation_id` (Ascending), `timestamp` (Ascending)
  - Fields: `recipient_id` (Ascending), `read` (Ascending)

## Troubleshooting

### Firebase not initializing

**Error:** `Firebase credentials not found`

**Solution:**
- Ensure `firebase-credentials.json` exists in the project root
- Check the file path in `settings.py`
- Verify the file is valid JSON

### Import errors

**Error:** `Import "firebase_admin" could not be resolved`

**Solution:**
```powershell
pip install firebase-admin google-cloud-firestore
```

### Messages not appearing in real-time

**Possible causes:**
1. **Polling not working** - Check browser console for errors
2. **CSRF token issues** - Ensure CSRF token is included in requests
3. **Firestore security rules** - Temporarily use relaxed rules to test

### Permission denied errors

**Error:** `PERMISSION_DENIED: Missing or insufficient permissions`

**Solution:**
- Review your Firestore security rules
- For development, use the relaxed rules (see Step 3)
- For production, ensure rules match your authentication setup

## Security Best Practices

1. **Never commit `firebase-credentials.json` to version control**
2. **Use production security rules** when deploying
3. **Implement proper authentication** before accessing Firestore
4. **Regularly rotate service account keys**
5. **Monitor Firestore usage** in Firebase Console
6. **Set up billing alerts** to avoid unexpected charges

## Monitoring and Usage

### View Messages in Firebase Console

1. Go to Firestore Database
2. Click on "Data" tab
3. Browse the `messages` collection
4. You can manually edit/delete documents here

### Monitor Usage

1. Go to "Usage" tab in Firestore Database
2. Monitor:
   - Document reads/writes
   - Storage usage
   - Network egress

### Pricing (Free Tier Limits)

- **Stored data:** 1 GiB
- **Document writes:** 20,000 per day
- **Document reads:** 50,000 per day
- **Document deletes:** 20,000 per day

For more details, visit: https://firebase.google.com/pricing

## Features Implemented

✅ Real-time message synchronization (via polling)
✅ Conversation-based messaging
✅ Unread message count
✅ User search for new conversations
✅ Message read status
✅ Support for all user roles (admin, principal, registrar, teacher, student, guardian)
✅ Responsive UI with dark mode support

## Future Enhancements (Optional)

- 🔄 True real-time updates using Firebase SDK on frontend
- 📎 File attachments in messages
- 🔔 Push notifications for new messages
- 🗑️ Message deletion
- ⭐ Message starring/flagging
- 📧 Email notifications for missed messages
- 🔍 Message search functionality
- 👥 Group messaging

## Support

For issues or questions:
1. Check Firebase documentation: https://firebase.google.com/docs/firestore
2. Review Django logs for errors
3. Check browser console for JavaScript errors
4. Verify Firestore security rules

---

**Last Updated:** November 22, 2025
**Created for:** PROTECH Attendance System
**Firebase Version:** Admin SDK 6.2.0+
