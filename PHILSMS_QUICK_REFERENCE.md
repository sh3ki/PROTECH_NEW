# PhilSMS Quick Reference

## ⚡ Quick Setup Checklist

- [x] Sign up at https://dashboard.philsms.com/
- [x] Get API token
- [x] Subscribe to free plan
- [ ] **ADD SMS CREDITS** (Important!)
- [ ] Configure sender ID (optional)
- [ ] Test integration

---

## 🔑 Your Credentials

**API Token:**
```
377|DT0C9GeHCgLXdNt5oxjajd3QqdLlKcqMHv5KLZcE3b45ab96
```

**API Endpoint:**
```
https://dashboard.philsms.com/api/v3/sms/send
```

---

## 💰 What to Do in PhilSMS Dashboard

### 1. **ADD CREDITS** (Required!) 
Without credits, SMS won't send even with free subscription.

**Steps:**
1. Login to https://dashboard.philsms.com/
2. Go to **Credits** or **Billing**
3. Purchase SMS credits package
4. Typical cost: ₱0.50-₱1.00 per SMS

### 2. **Register Sender ID** (Recommended)
Makes SMS appear from "PROTECH" instead of a number.

**Steps:**
1. Go to **Sender IDs** in dashboard
2. Click **Add Sender ID**
3. Enter: `PROTECH` or `PROTECH-ATT`
4. Wait for approval (1-3 days)

---

## 🧪 Testing

### Test the Integration:
```bash
python test_philsms.py
```

This will:
- ✅ Test phone number formatting
- ✅ Verify API configuration
- ✅ Send a test SMS to your phone

### Test with Real Student:
1. Ensure guardian has phone number in system
2. Use face recognition to time in
3. Check for both email AND SMS

---

## 📱 Phone Number Format

Guardians' phone numbers can be in any of these formats:
- `09171234567` ✅
- `9171234567` ✅
- `639171234567` ✅
- `+639171234567` ✅

System auto-converts to: `639171234567`

---

## 📧 What Guardians Receive

### Email (existing):
```
Subject: Student Time In Alert - Juan Dela Cruz

Dear Maria Dela Cruz,

This is to inform you that your child has arrived at school.

Student Details:
Name: Juan Santos Dela Cruz
Student ID: 123456789012
Grade & Section: Grade 7 - Section A

Time In Details:
Date: November 24, 2025
Time: 07:45 AM
Status: ON TIME
...
```

### SMS (new!):
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

---

## ⚠️ Important Notes

1. **Credits Required**: Free subscription doesn't include free SMS credits
2. **Cost**: ~₱0.50-₱1.00 per SMS
3. **Delivery**: Usually instant, up to 2 minutes
4. **Phone Numbers**: Must be Philippine mobile (09XX or 639XX)
5. **Monitoring**: Check dashboard for delivery status

---

## 🔧 Configuration Location

All settings in: `PROTECH/settings.py`

```python
PHILSMS_API_TOKEN = '377|DT0C9GeHCgLXdNt5oxjajd3QqdLlKcqMHv5KLZcE3b45ab96'
PHILSMS_SENDER_ID = 'PROTECH'  # After approval
```

---

## 🐛 Troubleshooting

### SMS not sending?
1. Check credits in PhilSMS dashboard
2. Verify API token is correct
3. Ensure guardian has valid phone number
4. Check terminal for error messages

### Getting errors?
```bash
# Check terminal output for:
SMS failed for 639123456789: [error message]
```

---

## 📊 Monitor Usage

**PhilSMS Dashboard:**
- SMS sent today/month
- Credit balance
- Delivery status
- Failed messages

**Important**: Set up low credit alerts!

---

## 🎯 Action Items (TO DO)

1. ⚠️ **ADD SMS CREDITS** - Cannot send without credits!
2. 🔄 Register sender ID "PROTECH" (optional)
3. ✅ Run `python test_philsms.py` to test
4. 📊 Set up credit alerts in dashboard
5. 🎓 Test with actual student time-in

---

## 📞 Support

- **PhilSMS**: support@philsms.com
- **Dashboard**: https://dashboard.philsms.com/
- **Docs**: https://dashboard.philsms.com/api/v3/documentation

---

**Ready to use!** Just add credits and test! 🚀
