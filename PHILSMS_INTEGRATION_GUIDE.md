# PhilSMS Integration Guide

## Overview
This guide explains how the PhilSMS API is integrated into the PROTECH Attendance System to send SMS notifications to guardians when students time in.

---

## Features Implemented

### 1. **SMS Notification on Time In**
When a student times in using face recognition:
- ✅ Email is sent to all guardians with email addresses
- ✅ SMS is sent to all guardians with phone numbers
- ✅ Both notifications contain the same information:
  - Student name and ID
  - Grade and section
  - Time in date and time
  - Attendance status (On Time/Late)

---

## PhilSMS Setup Steps

### 1. **Account Registration** ✅
- You've already signed up at https://dashboard.philsms.com/
- Account is created and active

### 2. **API Token** ✅
- Token obtained: `377|DT0C9GeHCgLXdNt5oxjajd3QqdLlKcqMHv5KLZcE3b45ab96`
- Token is configured in `settings.py`

### 3. **Free Subscription** ✅
- You've subscribed to the free plan (₱0)
- Free tier typically includes:
  - Limited SMS credits per month
  - Access to all API features
  - Standard delivery priority

---

## What You Need to Do Next in PhilSMS Dashboard

### 1. **Add SMS Credits** (Important!)
Even with the free subscription, you may need to purchase SMS credits:
- Go to: **Dashboard** → **Credits/Billing**
- Purchase SMS credits package
- Typical pricing:
  - ₱0.50 - ₱1.00 per SMS (varies by plan)
  - Bulk packages available for discounts

### 2. **Configure Sender ID** (Optional but Recommended)
A Sender ID is the name that appears as the sender of the SMS.

**Steps:**
1. Go to: **Dashboard** → **Sender IDs** or **Settings**
2. Click **"Add Sender ID"** or **"Register Sender ID"**
3. Enter your desired sender name: **`PROTECH`** or **`PROTECH-ATT`**
4. Submit for approval (may take 1-3 business days)
5. Once approved, update your `.env` file:
   ```
   PHILSMS_SENDER_ID=PROTECH
   ```

**Without a custom Sender ID:**
- SMS will be sent from a generic number or "PhilSMS"
- Still works perfectly, just less branded

### 3. **Check SMS Delivery Settings**
1. Go to: **Settings** → **API Settings** or **Delivery Settings**
2. Verify these settings:
   - ✅ API is enabled
   - ✅ Delivery reports enabled (optional, for tracking)
   - ✅ Default sender ID set (if configured)

### 4. **Review Pricing & Limits**
1. Go to: **Dashboard** → **Pricing** or **Account**
2. Check:
   - SMS rate per message
   - Monthly free SMS quota (if any)
   - Daily sending limits
   - API rate limits

### 5. **Test Phone Numbers** (Optional)
Some SMS providers allow you to add test numbers:
1. Go to: **Settings** → **Test Numbers**
2. Add your phone number for testing
3. Test messages may be free or discounted

---

## Configuration Files

### `.env` File (Create if not exists)
Add these lines to your `.env` file in the project root:

```env
# PhilSMS Configuration
PHILSMS_API_TOKEN=377|DT0C9GeHCgLXdNt5oxjajd3QqdLlKcqMHv5KLZcE3b45ab96
PHILSMS_SENDER_ID=PROTECH
```

### Phone Number Format
Guardian phone numbers in the database should be in one of these formats:
- `639XXXXXXXXX` (preferred - international format)
- `09XXXXXXXXX` (local format - will be auto-converted)
- `9XXXXXXXXX` (short format - will be auto-converted)
- `+639XXXXXXXXX` (with plus - will be auto-converted)

The system automatically converts all formats to `639XXXXXXXXX`.

---

## Testing the Integration

### 1. **Test with Face Recognition**
1. Make sure you have credits in your PhilSMS account
2. Ensure a guardian has a valid phone number
3. Use face recognition to time in a student
4. Check:
   - ✅ Email received
   - ✅ SMS received
   - ✅ Both contain same information

### 2. **Check Logs**
If SMS fails, check terminal output for error messages:
```
SMS failed for 639123456789: [error message]
```

### 3. **Monitor PhilSMS Dashboard**
1. Go to: **Dashboard** → **SMS Logs** or **History**
2. View:
   - Sent messages
   - Delivery status
   - Failed messages
   - Credit balance

---

## SMS Message Format

The SMS sent to guardians looks like this:

```
PROTECH Time In Alert

Student: Juan Dela Cruz
ID: 123456789012
Grade: Grade 7 - Section A
Date: Nov 24, 2025
Time: 07:45 AM
Status: ON TIME

-PROTECH Attendance System
```

**Message Length:** ~160 characters (1 SMS credit)

---

## Troubleshooting

### Issue: SMS not sending
**Solutions:**
1. ✅ Check API token is correct in settings
2. ✅ Verify you have sufficient SMS credits
3. ✅ Ensure phone number format is valid
4. ✅ Check PhilSMS dashboard for error logs
5. ✅ Verify API is enabled in PhilSMS settings

### Issue: Invalid phone number
**Solutions:**
- Guardian phone must be Philippine mobile number
- Must be 10-12 digits
- Check database for correct phone format

### Issue: SMS delayed
**Solutions:**
- Free tier may have lower priority
- Check network operator delays
- Verify in PhilSMS delivery reports

### Issue: API rate limit exceeded
**Solutions:**
- PhilSMS may limit requests per minute
- System handles this gracefully
- Check your plan's rate limits

---

## Important Notes

### 1. **Cost Considerations**
- Each SMS costs credits (typically ₱0.50-₱1.00)
- Monitor credit usage regularly
- Set up low credit alerts in PhilSMS dashboard
- Consider bulk credit packages for discounts

### 2. **Delivery Time**
- SMS typically delivers within seconds
- May take up to 1-2 minutes during peak hours
- Delivery depends on network operator

### 3. **Guardian Setup**
- Make sure guardians have valid phone numbers in the system
- Phone numbers must be Philippine mobile numbers
- SMS will only send if guardian has a phone number

### 4. **Privacy & Compliance**
- Only send SMS to registered guardians
- Include opt-out mechanism if required
- Follow Philippine data privacy laws

---

## Files Modified

1. **`PROTECHAPP/philsms_service.py`** (New)
   - PhilSMS API integration service
   - Phone number formatting
   - SMS sending logic

2. **`PROTECHAPP/views/face_recognition_views.py`**
   - Added SMS sending to time-in notification
   - Sends SMS alongside email

3. **`PROTECH/settings.py`**
   - Added PhilSMS configuration
   - API token and sender ID settings

4. **`requirements.txt`**
   - Added `requests>=2.31.0` dependency

---

## Next Steps (Action Required!)

1. ✅ **Add SMS Credits** to your PhilSMS account
2. ⏳ **Register Sender ID** (optional but recommended)
3. ✅ **Test the integration** with a real student time-in
4. ✅ **Monitor credit usage** in PhilSMS dashboard
5. ✅ **Set up credit alerts** to avoid running out

---

## API Documentation

Official PhilSMS API Docs: https://dashboard.philsms.com/api/v3/documentation

**Endpoint Used:** `POST https://dashboard.philsms.com/api/v3/sms/send`

**Request Format:**
```json
{
  "recipient": "639123456789",
  "message": "Your message here",
  "sender_id": "PROTECH"
}
```

**Headers:**
```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
Accept: application/json
```

---

## Support

- **PhilSMS Support:** support@philsms.com or dashboard support chat
- **API Issues:** Check dashboard logs and API documentation
- **Integration Issues:** Check terminal logs for error messages

---

**Integration Complete!** 🎉

The system now sends both EMAIL and SMS to guardians when students time in.
