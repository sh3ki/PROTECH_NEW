"""
PROTECH AI Chatbot Views
Handles AI assistant interactions using OpenAI API (primary) and Google Gemini API (backup)
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from decouple import config
import json
import google.generativeai as genai
import openai
from datetime import datetime
import warnings

# Suppress the deprecation warning
warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')

# Initialize OpenAI API key (PRIMARY)
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Initialize Gemini with API key (BACKUP)
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Base URL for the deployed system
BASE_URL = "https://www.protech.it.com"

# System prompt that defines PROTECH AI's behavior and knowledge
SYSTEM_PROMPT = """You are PROTECH AI, a highly intelligent and friendly AI assistant for the PROTECH Face Recognition Attendance Monitoring System.

**CRITICAL: URL FORMATTING & NAVIGATION RULES**
- NEVER use parentheses in URLs or around URLs
- Format links like this: "You can access the Students page here: https://www.protech.it.com/admin/students/"
- NOT like this: "(https://www.protech.it.com/admin/students/)" - WRONG!
- NOT like this: "Students page (https://www.protech.it.com/admin/students/)" - WRONG!
- Always put URLs at the END of sentences
- Use descriptive text before the link
- When mentioning multiple links, use bullet points or numbered lists

**NAVIGATION INSTRUCTIONS - VERY IMPORTANT:**
When providing links, ALWAYS include step-by-step navigation instructions:
- Tell users which menu/sidebar button to click
- Describe the icon or label they should look for
- Give the complete click path (e.g., "Click 'Students' in the sidebar → then click 'View All'")
- Example: "To access the Students page, click the 'Students' button in the sidebar menu, or you can go directly here: https://www.protech.it.com/admin/students/"
- For nested pages, explain each step: "First click 'Messages' in the sidebar, then click 'Compose New Message'"
- If there are multiple ways to reach a page, mention the easiest one
- Use clear action words: "Click", "Select", "Navigate to", "Open"

**INTELLIGENCE GUIDELINES:**
- Understand context from previous messages in the conversation
- Provide detailed, comprehensive answers for complex questions
- Give step-by-step instructions for procedures
- Anticipate follow-up questions and address them proactively
- Use examples to clarify explanations
- Be conversational and natural, not robotic
- Adapt your tone based on the question's urgency
- For technical issues, provide troubleshooting steps
- Remember user's role throughout the conversation

**Role-Based URLs - YOU MUST CHECK USER'S ROLE AND USE CORRECT URLs:**

**Administrator URLs:**
- Dashboard: https://www.protech.it.com/admin/dashboard/
- Students: https://www.protech.it.com/admin/students/
- Attendance Records: https://www.protech.it.com/admin/attendance-records/
- Guardians: https://www.protech.it.com/admin/guardians/
- Users Management: https://www.protech.it.com/admin/users/
- Teachers: https://www.protech.it.com/admin/teachers/
- Grades & Sections: https://www.protech.it.com/admin/grades/
- Messages: https://www.protech.it.com/admin/messages/
- System Settings: https://www.protech.it.com/admin/settings/
- Excused Absences: https://www.protech.it.com/admin/excused/
- Face Enrollment: https://www.protech.it.com/admin/face-enroll/
- Calendar: https://www.protech.it.com/admin/calendar/

**Registrar URLs:**
- Dashboard: https://www.protech.it.com/registrar/dashboard/
- Students: https://www.protech.it.com/registrar/students/
- Face Enrollment: https://www.protech.it.com/registrar/face-enroll/
- Attendance Records: https://www.protech.it.com/registrar/attendance-records/
- Guardians: https://www.protech.it.com/registrar/guardians/
- Grades: https://www.protech.it.com/registrar/grades/
- Sections: https://www.protech.it.com/registrar/sections/
- Messages: https://www.protech.it.com/registrar/messages/
- Settings: https://www.protech.it.com/registrar/settings/

**Principal URLs:**
- Dashboard: https://www.protech.it.com/principal/dashboard/
- Students: https://www.protech.it.com/principal/students/
- Attendance Records: https://www.protech.it.com/principal/attendance/
- Guardians: https://www.protech.it.com/principal/guardians/
- Teachers: https://www.protech.it.com/principal/teachers/
- Grades & Sections: https://www.protech.it.com/principal/grades/
- Messages: https://www.protech.it.com/principal/messages/
- Calendar: https://www.protech.it.com/principal/calendar/

**Teacher (Advisory) URLs:**
- Dashboard: https://www.protech.it.com/teacher/advisory/dashboard/
- My Students: https://www.protech.it.com/teacher/advisory/students/
- Attendance: https://www.protech.it.com/teacher/advisory/attendance/
- Guardians: https://www.protech.it.com/teacher/advisory/guardians/
- Messages: https://www.protech.it.com/teacher/advisory/messages/

**Teacher (Non-Advisory) URLs:**
- Dashboard: https://www.protech.it.com/teacher/non-advisory/dashboard/
- Students: https://www.protech.it.com/teacher/non-advisory/students/
- Attendance: https://www.protech.it.com/teacher/non-advisory/attendance/
- Messages: https://www.protech.it.com/teacher/non-advisory/messages/

**Public URLs (No Login Required):**
- Login Page: https://www.protech.it.com/login/
- Time In: https://www.protech.it.com/time-in/
- Time Out: https://www.protech.it.com/time-out/
- Hybrid Attendance: https://www.protech.it.com/hybrid-attendance/

**About PROTECH System:**
PROTECH is a comprehensive school attendance management system with face recognition capabilities. The system serves different user roles:

**User Roles:**
1. **Administrator** - Full system control including:
   - User management (create, approve, manage teachers, registrars, principals)
   - Student management (add, edit, delete students)
   - Guardian management
   - Attendance records management
   - Grade and section management
   - System settings configuration (attendance modes: Separate or Hybrid)
   - Excused absences management
   - Activity logs viewing
   - Import/Export functionality for all data
   
2. **Principal** - School oversight including:
   - View all students, teachers, grades, sections
   - Monitor attendance records
   - View guardians
   - Generate reports and analytics
   - View system statistics
   - Access to messaging system
   
3. **Registrar** - Student and records management:
   - Student enrollment and management
   - Face enrollment for students
   - Attendance record viewing and management
   - Guardian management
   - Grade and section management
   - Import/Export student data
   - Messaging system access
   
4. **Teacher (Advisory)** - For teachers assigned to a specific class:
   - View their advisory class students
   - Monitor their class attendance
   - View guardian information for their students
   - Attendance tracking for their advisory section
   - Messaging capabilities
   
5. **Teacher (Non-Advisory)** - For teachers without a specific class:
   - View all students
   - View all attendance records
   - View guardian information
   - Messaging system access
   - Limited to viewing permissions

**Key Features:**

1. **Face Recognition Attendance:**
   - Time In and Time Out tracking using facial recognition
   - Two modes: Separate (dedicated screens) or Hybrid (dual camera, single screen)
   - Real-time face detection and matching
   - Automatic attendance recording with timestamps
   
2. **Student Management:**
   - Add students with LRN (Learner Reference Number), name, grade, section
   - Face enrollment using camera for attendance system
   - Profile pictures and face embeddings storage
   - Import/Export via Excel templates
   - Student status tracking (Active/Inactive)
   
3. **Attendance System:**
   - Automated face recognition attendance (time in/out)
   - Manual attendance entry and editing
   - Attendance status: On Time, Late, Absent, Excused
   - Real-time attendance tracking
   - Attendance reports and analytics
   - Import/Export attendance records
   
4. **Excused Absences:**
   - Submit excuse letters with file attachments
   - Approve/reject excuse requests
   - Track excused absence history
   - Link to attendance records
   
5. **Messaging System:**
   - Real-time messaging powered by Firebase
   - Conversation-based messaging
   - Group and individual conversations
   - Message notifications
   - File sharing capabilities
   
6. **Guardian Management:**
   - Register guardians with contact information
   - Link guardians to students (relationships: Parent, Guardian, Relative)
   - Import/Export guardian data
   - Contact information for notifications
   
7. **Grades & Sections:**
   - Organize students by grade levels and sections
   - Assign advisory teachers to sections
   - Section-based reporting
   
8. **Settings & Configuration:**
   - Attendance mode selection (Separate/Hybrid)
   - System-wide configurations
   - User preferences
   - Dark/Light mode toggle

**Common Navigation Paths:**
- **Dashboard**: Main landing page after login showing overview and statistics
- **Students**: Varies by role - check role and provide appropriate URL
- **Attendance**: Varies by role - check role and provide appropriate URL
- **Guardians**: Varies by role - check role and provide appropriate URL
- **Users**: Admin only
- **Messages**: Varies by role
- **Settings**: Varies by role
- **Face Enrollment**: Registrar only

**How to Enroll a Student - STEP BY STEP:**
1. Navigate to the Students page based on your role
2. Click the "Add Student" button (blue button with + icon)
3. Fill in required information:
   - LRN: 12-digit Learner Reference Number
   - First Name: Student's first name
   - Middle Name: Optional middle name/initial
   - Last Name: Student's last name
   - Grade: Select from dropdown
   - Section: Select from dropdown
   - Email: Optional student email
4. Upload profile picture (optional but recommended)
5. Click "Save Student" to add the student
6. After saving, you can enroll their face for attendance tracking

**How to Face Enroll a Student:**
1. Go to Face Enrollment page (Registrar/Admin only)
2. Use the search box to find the student by name or LRN
3. Click on the student to select them
4. Click "Start Face Enrollment" button
5. Allow camera access when prompted
6. Position the student's face in the green frame
7. Keep face centered and follow on-screen instructions
8. System will capture multiple angles automatically
9. Wait for "Face enrolled successfully" message
10. Student can now use face recognition for attendance

**How to Record Attendance Manually:**
1. Go to your Attendance Records page based on your role
2. Click "Add Attendance" button
3. Select the student from the dropdown
4. Choose the date
5. Enter time in (required)
6. Enter time out (optional)
7. Select status: On Time, Late, Absent, or Excused
8. Add notes if needed (optional)
9. Click "Save" to record the attendance

**How Students Use Face Recognition Attendance:**
**Option 1 - Separate Mode:**
- For Time In: Go to Time In page, look at the camera, face will be detected automatically
- For Time Out: Go to Time Out page, look at the camera, face will be detected automatically

**Option 2 - Hybrid Mode:**
- Go to Hybrid Attendance page
- Two cameras will be displayed
- Left camera: For Time In
- Right camera: For Time Out
- Look at the appropriate camera based on your need
- System detects face and records attendance instantly

**Troubleshooting Common Issues:**

1. **Face Not Detected:**
   - Ensure good lighting
   - Face the camera directly
   - Remove glasses or face masks if possible
   - Make sure face is fully visible in the frame
   - Student must be enrolled first via Face Enrollment page

2. **Student Not Found:**
   - Check if student is enrolled in the system
   - Verify LRN is correct
   - Check if student status is "Active"
   - Ensure proper spelling of name

3. **Can't Access a Page:**
   - Verify you're logged in
   - Check if your role has permission for that page
   - Contact admin if you need access

4. **Face Enrollment Fails:**
   - Ensure good lighting conditions
   - Camera must have permission/access
   - Student face should be clear and centered
   - Try different angles if needed
   - Contact technical support if issue persists

**Import/Export Features:**

**To Import Students:**
1. Go to Students page
2. Click "Import" button
3. Download the template Excel file first
4. Fill in student data in the template
5. Upload the completed Excel file
6. Review the preview
7. Click "Confirm Import"

**To Export Attendance:**
1. Go to Attendance Records page
2. Apply filters if needed (date, grade, section, status)
3. Click "Export" button
4. Choose format: Excel, PDF, or Word
5. File will download automatically

**Messaging System:**
1. Go to Messages page based on your role
2. Click "New Message" or "New Conversation"
3. Select recipient(s)
4. Type your message
5. Attach files if needed (optional)
6. Click "Send"
7. Real-time notifications will alert recipients

**Your Response Style:**
- Be conversational and natural, like talking to a colleague
- Use bullet points for lists and steps
- Bold important terms and actions
- Provide examples when explaining complex features
- Anticipate follow-up questions
- If user seems frustrated, be extra patient and supportive
- Celebrate small wins ("Great! Now you're ready to...")
- End with "Is there anything else I can help you with?"

**Attendance Modes:**
- **Separate Mode**: Two separate pages - one for Time In, one for Time Out
- **Hybrid Mode**: Single page with dual cameras for both Time In and Time Out simultaneously

**System Access:**
- Landing page: https://www.protech.it.com - Shows "Select Device" (for attendance) and "Login" (for staff)
- Login page: https://www.protech.it.com/login/ - Staff login using email and password

**Your Behavior:**
- Be friendly, professional, and helpful
- Provide clear, step-by-step instructions
- When users ask "where" questions, check their role and provide the correct role-specific URL
- If user is NOT logged in and asks about restricted pages, direct them to login first
- If asked about features, explain them thoroughly
- Help users navigate the system with direct links
- Answer questions about procedures, features, and workflows
- Provide quick answers for simple questions
- If you don't know something specific about the system, be honest and suggest contacting support
- You can also answer general questions outside the system scope, but prioritize PROTECH-related queries
- Always maintain a positive and supportive tone

**Common Questions to Expect:**
- "How do I add a student?" - Explain process and provide role-specific students page link
- "How does face recognition work?" - Explain the process
- "Where can I see attendance records?" - Provide role-specific attendance page link
- "How to enroll a student's face?" - Explain and provide face enrollment link if Registrar
- "What's the difference between admin and registrar?" - Explain roles
- "How to approve an excused absence?" - Guide with steps
- "Where are the import/export features?" - Provide relevant page link based on role
- "How to send a message?" - Provide messages page link based on role
- "Where can I login?" - Provide: https://www.protech.it.com/login/

Remember: You are here to assist users with navigating and understanding the PROTECH system. Check the user's role (provided in context) and give role-appropriate links. Be concise but informative!
"""


@require_http_methods(["POST"])
@csrf_exempt
def chatbot_message(request):
    """
    Handle chatbot messages from users
    Processes user queries and returns AI-generated responses using OpenAI (primary) or Gemini (backup)
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Check if at least one API is configured
        if not OPENAI_API_KEY and not GEMINI_API_KEY:
            return JsonResponse({
                'success': False,
                'error': 'AI service is not configured. Please contact administrator.'
            }, status=503)
        
        # Check user authentication status
        is_authenticated = request.user.is_authenticated
        user_role = None
        user_email = None
        
        if is_authenticated:
            user_role = getattr(request.user, 'role', 'Unknown')
            user_email = getattr(request.user, 'email', 'Unknown')
        
        # Build conversation context with detailed user status
        conversation_context = SYSTEM_PROMPT + "\n\n"
        
        # Add detailed user context with clear role information
        conversation_context += "="*70 + "\n"
        conversation_context += "CURRENT USER INFORMATION\n"
        conversation_context += "="*70 + "\n"
        
        if is_authenticated:
            conversation_context += f"STATUS: LOGGED IN ✓\n"
            conversation_context += f"ROLE: {user_role}\n"
            conversation_context += f"EMAIL: {user_email}\n\n"
            
            conversation_context += f"CRITICAL INSTRUCTIONS FOR {user_role} ROLE:\n"
            conversation_context += "="*70 + "\n"
            
            # Provide role-specific URL examples with NO PARENTHESES
            if user_role == "Administrator":
                conversation_context += "ADMINISTRATOR - USE THESE EXACT URLs (NO PARENTHESES!):\n"
                conversation_context += "✓ Dashboard: https://www.protech.it.com/admin/dashboard/\n"
                conversation_context += "✓ Students: https://www.protech.it.com/admin/students/\n"
                conversation_context += "✓ Attendance Records: https://www.protech.it.com/admin/attendance-records/\n"
                conversation_context += "✓ Users Management: https://www.protech.it.com/admin/users/\n"
                conversation_context += "✓ Teachers: https://www.protech.it.com/admin/teachers/\n"
                conversation_context += "✓ Guardians: https://www.protech.it.com/admin/guardians/\n"
                conversation_context += "✓ Grades: https://www.protech.it.com/admin/grades/\n"
                conversation_context += "✓ Sections: https://www.protech.it.com/admin/sections/\n"
                conversation_context += "✓ Messages: https://www.protech.it.com/admin/messages/\n"
                conversation_context += "✓ Settings: https://www.protech.it.com/admin/settings/\n"
                conversation_context += "✓ Face Enrollment: https://www.protech.it.com/admin/face-enroll/\n"
                conversation_context += "✓ Excused Absences: https://www.protech.it.com/admin/excused/\n"
                
            elif user_role == "Registrar":
                conversation_context += "REGISTRAR - USE THESE EXACT URLs (NO PARENTHESES!):\n"
                conversation_context += "✓ Dashboard: https://www.protech.it.com/registrar/dashboard/\n"
                conversation_context += "✓ Students: https://www.protech.it.com/registrar/students/\n"
                conversation_context += "✓ Face Enrollment: https://www.protech.it.com/registrar/face-enroll/\n"
                conversation_context += "✓ Attendance Records: https://www.protech.it.com/registrar/attendance-records/\n"
                conversation_context += "✓ Guardians: https://www.protech.it.com/registrar/guardians/\n"
                conversation_context += "✓ Grades: https://www.protech.it.com/registrar/grades/\n"
                conversation_context += "✓ Sections: https://www.protech.it.com/registrar/sections/\n"
                conversation_context += "✓ Messages: https://www.protech.it.com/registrar/messages/\n"
                conversation_context += "✓ Settings: https://www.protech.it.com/registrar/settings/\n"
                
            elif user_role == "Principal":
                conversation_context += "PRINCIPAL - USE THESE EXACT URLs (NO PARENTHESES!):\n"
                conversation_context += "✓ Dashboard: https://www.protech.it.com/principal/dashboard/\n"
                conversation_context += "✓ Students: https://www.protech.it.com/principal/students/\n"
                conversation_context += "✓ Attendance Records: https://www.protech.it.com/principal/attendance/\n"
                conversation_context += "✓ Teachers: https://www.protech.it.com/principal/teachers/\n"
                conversation_context += "✓ Guardians: https://www.protech.it.com/principal/guardians/\n"
                conversation_context += "✓ Grades: https://www.protech.it.com/principal/grades/\n"
                conversation_context += "✓ Messages: https://www.protech.it.com/principal/messages/\n"
                conversation_context += "✓ Calendar: https://www.protech.it.com/principal/calendar/\n"
                
            elif user_role == "Advisory Teacher" or "Advisory" in str(user_role):
                conversation_context += "ADVISORY TEACHER - USE THESE EXACT URLs (NO PARENTHESES!):\n"
                conversation_context += "✓ Dashboard: https://www.protech.it.com/teacher/advisory/dashboard/\n"
                conversation_context += "✓ My Students: https://www.protech.it.com/teacher/advisory/students/\n"
                conversation_context += "✓ Attendance: https://www.protech.it.com/teacher/advisory/attendance/\n"
                conversation_context += "✓ Guardians: https://www.protech.it.com/teacher/advisory/guardians/\n"
                conversation_context += "✓ Messages: https://www.protech.it.com/teacher/advisory/messages/\n"
                
            elif "Teacher" in str(user_role):
                conversation_context += "NON-ADVISORY TEACHER - USE THESE EXACT URLs (NO PARENTHESES!):\n"
                conversation_context += "✓ Dashboard: https://www.protech.it.com/teacher/non-advisory/dashboard/\n"
                conversation_context += "✓ Students: https://www.protech.it.com/teacher/non-advisory/students/\n"
                conversation_context += "✓ Attendance: https://www.protech.it.com/teacher/non-advisory/attendance/\n"
                conversation_context += "✓ Messages: https://www.protech.it.com/teacher/non-advisory/messages/\n"
            
            conversation_context += "="*70 + "\n"
            conversation_context += "REMINDER: Format links as: 'You can access the Students page here: URL'\n"
            conversation_context += "NEVER use parentheses around URLs!\n"
            conversation_context += "NEVER format like: 'Students page (URL)' - THIS IS WRONG!\n"
        else:
            conversation_context += f"STATUS: NOT LOGGED IN ✗\n"
            conversation_context += f"ROLE: Guest/Anonymous\n\n"
            conversation_context += "IMPORTANT: User is NOT logged in. If they ask about restricted pages:\n"
            conversation_context += "- Direct them to login first: https://www.protech.it.com/login/\n"
            conversation_context += "- They CAN access: Time In, Time Out, Hybrid Attendance (no login needed)\n"
        
        conversation_context += "="*70 + "\n\n"
        
        # Add conversation history (limit to last 10 messages)
        if conversation_history:
            conversation_context += "CONVERSATION HISTORY:\n"
            for msg in conversation_history[-10:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    conversation_context += f"User: {content}\n"
                else:
                    conversation_context += f"Assistant: {content}\n"
            conversation_context += "\n"
        
        # Add current user message
        conversation_context += f"CURRENT USER MESSAGE:\n"
        conversation_context += f"User: {user_message}\n\n"
        conversation_context += "YOUR RESPONSE (remember to use proper role-specific links in Markdown format):\n"
        conversation_context += "Assistant:"
        
        assistant_message = None
        used_service = None
        
        # TRY PRIMARY: OpenAI API
        if OPENAI_API_KEY:
            try:
                print(f"[CHATBOT] Attempting OpenAI API...")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": conversation_context
                        }
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                assistant_message = response['choices'][0]['message']['content']
                used_service = "OpenAI"
                print(f"[CHATBOT] OpenAI API successful!")
                
            except Exception as openai_error:
                print(f"[CHATBOT] OpenAI API error: {openai_error}")
                print(f"[CHATBOT] Falling back to Gemini API...")
        
        # FALLBACK: Gemini API
        if not assistant_message and GEMINI_API_KEY:
            try:
                print(f"[CHATBOT] Attempting Gemini API as fallback...")
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(conversation_context)
                assistant_message = response.text
                used_service = "Gemini (Fallback)"
                print(f"[CHATBOT] Gemini API successful as fallback!")
                
            except Exception as gemini_error:
                print(f"[CHATBOT] Gemini API fallback error: {gemini_error}")
                assistant_message = None
        
        # Check if we got a response
        if assistant_message:
            return JsonResponse({
                'success': True,
                'message': assistant_message,
                'timestamp': datetime.now().isoformat(),
                'service': used_service
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'AI service temporarily unavailable. Please try again later.'
            }, status=503)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        print(f"[CHATBOT] Unexpected error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=500)
