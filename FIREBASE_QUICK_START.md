# 🔥 Quick Firebase Firestore Setup Guide

Follow these steps to set up Firebase Firestore for your PROTECH messaging system.

---

## Step 1: Create Firebase Project (5 minutes)

### 1.1 Go to Firebase Console
- Open your browser and go to: **https://console.firebase.google.com/**
- Sign in with your Google account

### 1.2 Create New Project
1. Click **"Add project"** or **"Create a project"**
2. **Project name**: Enter `PROTECH-Messaging` (or any name you prefer)
3. Click **Continue**
4. **Google Analytics**: You can disable this (not needed for messaging)
5. Click **Create project**
6. Wait for project creation (takes ~30 seconds)
7. Click **Continue** when ready

---

## Step 2: Enable Firestore Database (3 minutes)

### 2.1 Create Firestore Database
1. In the left sidebar, click **"Build"** → **"Firestore Database"**
2. Click **"Create database"** button
3. **Choose location**:
   - Select **"Start in test mode"** (for development)
   - Click **Next**
4. **Select location**: Choose the closest region to you
   - Example: `asia-southeast1` (Singapore) for Southeast Asia
   - Click **Enable**
5. Wait for Firestore to be created (~1 minute)

### 2.2 Set Up Security Rules (Important!)
1. Go to **"Rules"** tab in Firestore Database
2. You'll see default test mode rules - **these expire in 30 days**
3. For now, keep test mode rules (we'll update later for production)

**Test Mode Rules** (temporary - for development only):
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.time < timestamp.date(2026, 1, 22);
    }
  }
}
```

⚠️ **Warning**: These rules allow anyone to read/write. Only use during development!

---

## Step 3: Get Service Account Key (API Credentials) ⭐ IMPORTANT

### 3.1 Access Project Settings
1. Click the **⚙️ (gear icon)** next to "Project Overview" at the top left
2. Click **"Project settings"**

### 3.2 Generate Service Account Key
1. Go to the **"Service accounts"** tab
2. You'll see **"Firebase Admin SDK"** section
3. Click **"Generate new private key"** button
4. A popup appears - Click **"Generate key"**
5. A JSON file will download automatically
   - Filename will be like: `protech-messaging-firebase-adminsdk-xxxxx-xxxxxxxxxx.json`

### 3.3 Save the Credentials File
1. **Rename** the downloaded file to: `firebase-credentials.json`
2. **Move** it to your Django project root folder:
   ```
   C:\Users\USER\Documents\SYSTEMS\WEB\PYTHON\DJANGO\PROTECH_NEW\firebase-credentials.json
   ```

⚠️ **SECURITY WARNING**: 
- **NEVER** commit this file to Git/GitHub
- **NEVER** share this file publicly
- Keep it secure like a password

---

## Step 4: Configure Django Project (2 minutes)

### 4.1 Add Credentials Path to .env (Optional but Recommended)

Create or edit `.env` file in your project root:

```env
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=C:\Users\USER\Documents\SYSTEMS\WEB\PYTHON\DJANGO\PROTECH_NEW\firebase-credentials.json
```

### 4.2 Add to .gitignore (IMPORTANT!)

Create or edit `.gitignore` file in your project root:

```
# Firebase credentials - NEVER commit these!
firebase-credentials.json
*.json

# Environment variables
.env

# Python
__pycache__/
*.pyc
*.pyo
venv/
.venv/
```

---

## Step 5: Test Firebase Connection (2 minutes)

### 5.1 Restart Django Server
1. Stop the server if running (Ctrl+C)
2. Start it again:
   ```powershell
   python manage.py runserver
   ```

### 5.2 Check for Success Message
Look for this in the console output:
```
Firebase initialized successfully
```

If you see this, Firebase is working! ✅

If you see errors:
- ❌ `Firebase credentials not found` → Check file path and name
- ❌ `Permission denied` → Check Firestore security rules
- ❌ `Invalid credentials` → Re-download the service account key

---

## Step 6: Test the Messaging Feature (5 minutes)

### 6.1 Access Messages Page
1. Start your Django server
2. Login to your application
3. Navigate to: **http://127.0.0.1:8000/admin/messages/**

### 6.2 Start a Conversation
1. Click **"New Message"** button
2. Type a name in the search box
3. Select a user from the results
4. Type a message and press **Enter** or click **Send**

### 6.3 Test Real-time Updates
1. Open another browser (or incognito window)
2. Login as a different user
3. Both users should see the conversation update automatically
4. Messages appear in real-time (updates every 5 seconds)

---

## 🎯 What You Should See in Firebase Console

### View Your Messages in Firestore
1. Go to Firebase Console → **Firestore Database** → **Data** tab
2. You should see a collection called **"messages"**
3. Click to expand and see your messages
4. Each message document contains:
   - `sender_id`, `sender_name`, `sender_role`
   - `recipient_id`, `recipient_name`, `recipient_role`
   - `message` (the text)
   - `timestamp`
   - `read` (boolean)
   - `conversation_id`

### Monitor Usage
1. Go to **"Usage"** tab
2. See:
   - Document reads
   - Document writes
   - Storage used

---

## 📊 Firebase Free Tier Limits

You get for FREE every day:
- ✅ **50,000 document reads**
- ✅ **20,000 document writes**
- ✅ **20,000 document deletes**
- ✅ **1 GB storage**

This is more than enough for a school messaging system!

---

## 🔒 Production Security Rules (Use Later)

When ready for production, update Firestore rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /messages/{messageId} {
      // Only authenticated users can read their own messages
      allow read: if request.auth != null && 
                     (resource.data.sender_id == request.auth.uid || 
                      resource.data.recipient_id == request.auth.uid);
      
      // Only authenticated users can create messages as themselves
      allow create: if request.auth != null && 
                       request.resource.data.sender_id == request.auth.uid;
      
      // Recipients can update messages (for read status)
      allow update: if request.auth != null && 
                       resource.data.recipient_id == request.auth.uid;
      
      // No deletes for now
      allow delete: if false;
    }
  }
}
```

**Note**: These production rules require Firebase Authentication, which we're not using yet. For now, stick with test mode rules.

---

## 🆘 Troubleshooting

### Problem: "Firebase credentials not found"
**Solution**: 
- Check file exists: `C:\Users\USER\Documents\SYSTEMS\WEB\PYTHON\DJANGO\PROTECH_NEW\firebase-credentials.json`
- Check filename is exactly `firebase-credentials.json`
- Check file has content (should be JSON with keys)

### Problem: "Module not found: firebase_admin"
**Solution**:
```powershell
.\venv\Scripts\pip install firebase-admin google-cloud-firestore
```

### Problem: Messages not appearing
**Solution**:
- Check browser console (F12) for JavaScript errors
- Verify Firebase initialized successfully in Django console
- Check Firestore rules in Firebase Console
- Try test mode rules temporarily

### Problem: CORS errors
**Solution**: 
- This shouldn't happen since we're using server-side Firebase
- If it does, check that requests go through Django backend

---

## ✅ Quick Checklist

- [ ] Firebase project created
- [ ] Firestore Database enabled
- [ ] Service account key downloaded
- [ ] `firebase-credentials.json` in project root
- [ ] `.gitignore` updated
- [ ] Django server shows "Firebase initialized successfully"
- [ ] Messages page loads without errors
- [ ] Can send a test message
- [ ] Message appears in Firebase Console

---

## 📚 Helpful Links

- Firebase Console: https://console.firebase.google.com/
- Firestore Documentation: https://firebase.google.com/docs/firestore
- Firebase Pricing: https://firebase.google.com/pricing
- Security Rules: https://firebase.google.com/docs/firestore/security/get-started

---

## 🎉 You're Done!

Once you complete all steps, your real-time messaging system is live!

Users can:
- ✅ Send messages to each other
- ✅ See conversations update in real-time
- ✅ Track unread messages
- ✅ Search for users to message
- ✅ View message history

**Need help?** Check the detailed `FIREBASE_SETUP.md` in your project root for more information.
