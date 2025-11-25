# 🔥 Firebase Web SDK Setup - URGENT

## Your Project ID: `protech-d12cc`

## Step 1: Get Firebase Web Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/project/protech-d12cc/settings/general)
2. Scroll down to **"Your apps"** section
3. **If you see a web app (</> icon)**, click the config icon (</>) to view credentials
4. **If you DON'T see a web app**, click **"Add app"** → Choose **Web** (</>) → Register app

## Step 2: Copy the Config Object

You'll see something like:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "protech-d12cc.firebaseapp.com",
  projectId: "protech-d12cc",
  storageBucket: "protech-d12cc.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef123456"
};
```

## Step 3: Add to .env File

Open your `.env` file and add these lines:

```env
# Firebase Web SDK Configuration
FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
FIREBASE_AUTH_DOMAIN=protech-d12cc.firebaseapp.com
FIREBASE_PROJECT_ID=protech-d12cc
FIREBASE_STORAGE_BUCKET=protech-d12cc.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abcdef123456
```

**Replace the values with YOUR actual values from Firebase Console!**

## Step 4: Restart Django Server

After adding credentials to `.env`:

```powershell
# Stop the server (Ctrl+C)
# Then restart:
python manage.py runserver
```

## Quick Test

After restarting, the error should be gone. Check browser console - you should see:
```
✓ Firebase real-time messaging initialized
```

Instead of:
```
❌ [code=invalid-argument]: Invalid resource field value
```

---

## Why This Error Happened

The Firebase Web SDK tried to connect to:
```
projects//databases/(default)  ← Notice the double slash!
```

This happened because `FIREBASE_PROJECT_ID` was empty in `.env`, so it became:
```
projects/${projectId}/databases/(default)
projects//databases/(default)  ← projectId was empty string
```

Once you add the credentials to `.env`, it will be:
```
projects/protech-d12cc/databases/(default)  ← Correct!
```
