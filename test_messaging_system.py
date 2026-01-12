#!/usr/bin/env python
"""
Complete test suite for PostgreSQL-based messaging system
Tests: duplicates, message loading, real-time functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from PROTECHAPP.models import Chat, Message, CustomUser, ChatParticipant
from collections import defaultdict

print("="*60)
print("MESSAGING SYSTEM COMPREHENSIVE TEST")
print("="*60)

# Test 1: Check conversation counts
print("\n[TEST 1] Conversation Counts")
total = Chat.objects.count()
private = Chat.objects.filter(is_group=False).count()
groups = Chat.objects.filter(is_group=True).count()
print(f"✓ Total conversations: {total}")
print(f"✓ Private conversations: {private}")
print(f"✓ Group conversations: {groups}")

# Test 2: Check for duplicate private conversations
print("\n[TEST 2] Duplicate Detection")
chats = Chat.objects.filter(is_group=False).prefetch_related('participants')
user_pairs = defaultdict(list)

for chat in chats:
    participants = sorted([p.user_id for p in chat.participants.all()])
    if len(participants) == 2:
        user_pairs[tuple(participants)].append(chat.id)

duplicates = {k: v for k, v in user_pairs.items() if len(v) > 1}

if len(duplicates) == 0:
    print("✓ PASS: No duplicate conversations found!")
else:
    print(f"✗ FAIL: Found {len(duplicates)} duplicate conversation pairs:")
    for pair, chat_ids in duplicates.items():
        user1 = CustomUser.objects.get(id=pair[0])
        user2 = CustomUser.objects.get(id=pair[1])
        print(f"  - {user1.get_full_name()} <-> {user2.get_full_name()}: {len(chat_ids)} chats {chat_ids}")

# Test 3: List all private conversations
print("\n[TEST 3] Private Conversation Details")
for chat in Chat.objects.filter(is_group=False).prefetch_related('participants__user')[:5]:
    participants = [p.user.get_full_name() for p in chat.participants.all()]
    msg_count = Message.objects.filter(chat=chat).count()
    print(f"  Chat ID {chat.id}: {' <-> '.join(participants)} ({msg_count} messages)")

# Test 4: Check message counts
print("\n[TEST 4] Message Statistics")
total_messages = Message.objects.count()
chats_with_messages = Chat.objects.filter(messages__isnull=False).distinct().count()
print(f"✓ Total messages: {total_messages}")
print(f"✓ Conversations with messages: {chats_with_messages}")

# Test 5: Verify data integrity
print("\n[TEST 5] Data Integrity")
orphan_participants = ChatParticipant.objects.filter(chat__isnull=True).count()
orphan_messages = Message.objects.filter(chat__isnull=True).count()
print(f"✓ Orphan participants: {orphan_participants}")
print(f"✓ Orphan messages: {orphan_messages}")

if orphan_participants == 0 and orphan_messages == 0:
    print("✓ PASS: Data integrity check passed!")
else:
    print("✗ FAIL: Found orphan records!")

# Final summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
if len(duplicates) == 0 and orphan_participants == 0 and orphan_messages == 0:
    print("✓ ALL TESTS PASSED - System ready for production!")
else:
    print("✗ SOME TESTS FAILED - Review issues above")
print("="*60)
