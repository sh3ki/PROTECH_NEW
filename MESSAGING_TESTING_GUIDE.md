# 🧪 PROTECH Messaging System - Testing Guide

## Quick Test Checklist

### ✅ Prerequisites
- [x] Django server running on http://127.0.0.1:8000/
- [x] Firebase configured (firebase-credentials.json)
- [x] At least 2 user accounts created

---

## 🔹 Test 1: Private Chat (1-on-1)

### Steps:
1. **Login as Admin**
   - Go to: http://127.0.0.1:8000/login/
   - Enter admin credentials
   
2. **Navigate to Messages**
   - Click "Messages" in sidebar
   - URL: http://127.0.0.1:8000/admin/messages/

3. **Create New Conversation**
   - Click "New Message" button
   - Modal opens with "Private Chat" tab active
   
4. **Search for User**
   - Type user name or email in search box
   - Wait 300ms for search results
   - Example: Search "teacher" or "student"

5. **Start Conversation**
   - Click on a user from search results
   - Conversation opens automatically
   - Chat area appears on right side

6. **Send Message**
   - Type: "Hello, this is a test message"
   - Press Enter or click Send button
   - Message appears instantly in chat area

7. **Verify Message Sent**
   - Check message shows on right side (sent by you)
   - Check blue background color
   - Check "✓ Sent" status below message
   - Check timestamp

8. **Open New Browser/Incognito**
   - Login as the recipient user
   - Go to Messages page
   - Check red unread badge appears
   - Check conversation shows in list

9. **View Message**
   - Click on conversation
   - Message appears on left side (received)
   - Check gray background color
   - Messages auto-marked as read

10. **Reply**
    - Type: "Reply test message"
    - Send message
    - Check it appears on right side

11. **Check Original User**
    - Go back to admin's browser
    - Wait 5 seconds (for polling)
    - Reply appears automatically
    - Check "✓✓ Read" status on original message

**Expected Results:**
- ✅ Conversation created successfully
- ✅ Messages send instantly
- ✅ Real-time updates work (5-second polling)
- ✅ Read/unread status updates
- ✅ Unread badge shows correct count
- ✅ Last message preview updates

---

## 🔹 Test 2: Group Chat

### Steps:
1. **Login as Admin**
   - Navigate to Messages page

2. **Create Group**
   - Click "New Message" button
   - Switch to "Group Chat" tab
   
3. **Configure Group**
   - Group Name: "Test Group Chat"
   - Click in participant search field
   
4. **Add Participants**
   - Search for first user
   - Click to select (blue checkmark appears)
   - Search for second user
   - Click to select
   - Search for third user
   - Click to select
   - Check "Selected Participants" shows 3 users

5. **Create Group**
   - Click "Create Group" button
   - Modal closes
   - Group appears in conversation list
   - Group has green icon with people symbol
   - Shows "(3 members)" next to name

6. **Send Group Message**
   - Type: "Welcome to the test group!"
   - Press Send
   - Message appears in chat

7. **Test as Group Member**
   - Open incognito browser
   - Login as one of the group members
   - Go to Messages
   - Check group appears in conversation list
   - Check unread badge shows "1"
   - Open group conversation
   - Message visible with sender name above it

8. **Reply in Group**
   - Type: "Thanks for adding me!"
   - Send message
   - Message appears

9. **Add More Participants**
   - As admin, click "Add Members" button
   - Search for another user
   - Select and add
   - Check member count updates to "(4 members)"
   
10. **Verify All Members See Updates**
    - Login as different group members
    - Check all see messages
    - Check all can send messages
    - Check sender names appear on messages

**Expected Results:**
- ✅ Group created with custom name
- ✅ Multiple participants added
- ✅ All members see messages
- ✅ Sender names shown in group chat
- ✅ Can add more participants
- ✅ Member count accurate
- ✅ Group icon visible (green with people)

---

## 🔹 Test 3: Read/Unread Tracking

### Steps:
1. **As User A**: Send message to User B
2. **Before User B reads**:
   - Check User B's unread badge (should show "1")
   - Check conversation list shows unread count
   - Check message status shows "✓ Sent"

3. **As User B**: 
   - Login and go to Messages
   - Check red badge shows unread count
   - Open conversation
   - Messages auto-marked as read

4. **As User A**:
   - Wait 5-10 seconds for polling
   - Check message status updates to "✓✓ Read"
   - Check conversation's unread count is 0

**Expected Results:**
- ✅ Unread count increments when message sent
- ✅ Badge shows on sidebar and conversation
- ✅ Auto-mark as read when viewing
- ✅ Read status syncs to sender
- ✅ Total unread count accurate

---

## 🔹 Test 4: Real-time Polling

### Steps:
1. **Open two browser windows side by side**
   - Window 1: Login as User A
   - Window 2: Login as User B
   - Both on Messages page

2. **Start Conversation**
   - User A sends message to User B
   
3. **Observe Real-time Updates**:
   - **In Window 2 (User B)**:
     - Wait up to 5 seconds
     - Conversation appears in list
     - Unread badge updates
   
4. **Test Message Polling**:
   - User B opens conversation
   - User A sends another message
   - **In Window 2**: 
     - Wait up to 5 seconds
     - New message appears automatically
   
5. **Test Read Status Polling**:
   - User B reads messages
   - **In Window 1 (User A)**:
     - Wait 5-10 seconds
     - Message status updates to "✓✓ Read"

**Expected Results:**
- ✅ New messages appear within 5 seconds
- ✅ Conversation list updates automatically
- ✅ Unread count updates automatically
- ✅ Read status syncs within 10 seconds
- ✅ No page refresh needed

---

## 🔹 Test 5: User Search

### Steps:
1. **Open New Message Modal**
   - Click "New Message" button

2. **Test Search Variations**:
   - Search by first name: "John"
   - Search by last name: "Doe"
   - Search by email: "john@"
   - Search by partial: "joh"
   
3. **Verify Results**:
   - Results appear after 300ms delay
   - Shows user avatar (initial)
   - Shows full name
   - Shows email address
   - Shows role (admin, teacher, student, etc.)
   
4. **Test Empty Search**:
   - Clear search box
   - Check results clear

5. **Test No Results**:
   - Search: "xyzabc123notfound"
   - Check shows "No users found"

**Expected Results:**
- ✅ Search works by name and email
- ✅ Results appear quickly (300ms debounce)
- ✅ User info displayed correctly
- ✅ Can click user to start conversation
- ✅ Empty search clears results

---

## 🔹 Test 6: UI/UX Features

### Check These Elements:

**Conversation List**:
- ✅ User avatars show initial letter
- ✅ Last message preview truncates
- ✅ Timestamps show relative time (e.g., "5m ago")
- ✅ Active conversation highlighted
- ✅ Unread badges visible

**Chat Area**:
- ✅ Messages align correctly (sent=right, received=left)
- ✅ Color coding (blue=sent, gray=received)
- ✅ Sender names in group chats
- ✅ Auto-scroll to bottom on new message
- ✅ Multi-line messages display correctly

**Modals**:
- ✅ Can close with X button
- ✅ Can close by clicking outside
- ✅ Tab switching works (Private/Group)
- ✅ Participant selection visual feedback

**Animations**:
- ✅ Messages fade in smoothly
- ✅ Hover effects on conversations
- ✅ Button transitions

---

## 🔹 Test 7: Error Handling

### Test These Scenarios:

1. **Empty Message**:
   - Try to send empty message
   - Should be prevented

2. **No Conversation Selected**:
   - Type in message input without selecting conversation
   - Should not allow sending

3. **Network Error Simulation**:
   - Open DevTools → Network tab
   - Set offline mode
   - Try to send message
   - Check error handling

4. **Invalid User Search**:
   - Search with special characters
   - Should handle gracefully

**Expected Results:**
- ✅ Empty messages blocked
- ✅ Error messages displayed
- ✅ UI remains functional
- ✅ No JavaScript console errors

---

## 📊 Performance Tests

### Check These Metrics:

1. **Message Load Time**:
   - Open conversation with 50+ messages
   - Should load within 2 seconds

2. **Search Response Time**:
   - Type in search box
   - Results within 500ms

3. **Real-time Update Delay**:
   - Send message
   - Recipient sees within 5 seconds

4. **Unread Count Accuracy**:
   - Send 10 messages
   - Unread count should be exactly 10

---

## 🐛 Common Issues & Solutions

### Issue 1: Messages not appearing
**Solution**: 
- Check browser console for errors
- Verify Firebase credentials
- Check network tab for failed requests
- Ensure polling is active

### Issue 2: Unread count incorrect
**Solution**:
- Clear browser cache
- Check mark_as_read API call
- Verify read_by array in Firestore
- Restart polling

### Issue 3: Search not working
**Solution**:
- Check search query parameters
- Verify user data exists
- Check API endpoint response
- Clear search input and retry

### Issue 4: Modal not closing
**Solution**:
- Click X button
- Click outside modal
- Check JavaScript console
- Refresh page

---

## 📝 Test Report Template

```
Date: _________________
Tester: _______________

Private Chat Test:     [ ] Pass  [ ] Fail
Group Chat Test:       [ ] Pass  [ ] Fail
Read/Unread Test:      [ ] Pass  [ ] Fail
Real-time Polling:     [ ] Pass  [ ] Fail
User Search:           [ ] Pass  [ ] Fail
UI/UX Features:        [ ] Pass  [ ] Fail
Error Handling:        [ ] Pass  [ ] Fail

Issues Found:
1. ____________________________
2. ____________________________
3. ____________________________

Notes:
_________________________________
_________________________________
_________________________________

Overall Status: [ ] Ready for Production  [ ] Needs Fixes
```

---

## 🎯 Success Criteria

All tests should pass with:
- ✅ No JavaScript console errors
- ✅ All features working as expected
- ✅ Real-time updates functioning
- ✅ Data persisting in Firestore
- ✅ UI responsive and smooth
- ✅ No performance issues

**When all tests pass**: System is ready for production use! 🎉

---

## 📞 Need Help?

Check these resources:
1. `MESSAGING_SYSTEM_COMPLETE.md` - Complete system overview
2. `FIREBASE_SETUP.md` - Firebase configuration
3. `FIREBASE_QUICK_START.md` - Quick reference
4. Browser DevTools Console - JavaScript errors
5. Django Server Console - Backend errors
6. Firestore Console - Data verification

**Happy Testing!** 🚀
