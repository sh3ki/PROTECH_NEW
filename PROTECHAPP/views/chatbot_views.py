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
SYSTEM_PROMPT = """You are PROTECH AI, a friendly and helpful AI assistant for the PROTECH Face Recognition Attendance Monitoring System.

**IMPORTANT: Link Guidelines**
When providing links:
- Use proper format: "You can access it here: https://www.protech.it.com/page/"
- Check user's role and provide role-specific URLs
- Use complete URLs starting with https://www.protech.it.com

**Role-Based URLs - CHECK USER'S ROLE:**

**Administrator:**
- Students: https://www.protech.it.com/admin/students/
- Attendance: https://www.protech.it.com/admin/attendance/
- Guardians: https://www.protech.it.com/admin/guardians/
- Users: https://www.protech.it.com/admin/users/
- Messages: https://www.protech.it.com/admin/messages/
- Settings: https://www.protech.it.com/admin/settings/
- Grades: https://www.protech.it.com/admin/grades/
- Sections: https://www.protech.it.com/admin/sections/

**Registrar:**
- Students: https://www.protech.it.com/registrar/students/
- Face Enrollment: https://www.protech.it.com/registrar/face-enroll/
- Attendance: https://www.protech.it.com/registrar/attendance/
- Guardians: https://www.protech.it.com/registrar/guardians/
- Messages: https://www.protech.it.com/registrar/messages/
- Settings: https://www.protech.it.com/registrar/settings/

**Principal:**
- Students: https://www.protech.it.com/principal/students/
- Attendance: https://www.protech.it.com/principal/attendance/
- Guardians: https://www.protech.it.com/principal/guardians/
- Messages: https://www.protech.it.com/principal/messages/

**Teacher:**
- Students: https://www.protech.it.com/teacher/students/
- Attendance: https://www.protech.it.com/teacher/attendance/
- Guardians: https://www.protech.it.com/teacher/guardians/
- Messages: https://www.protech.it.com/teacher/messages/

**Public (no login):**
- Login: https://www.protech.it.com/login/
- Time In: https://www.protech.it.com/time-in/
- Time Out: https://www.protech.it.com/time-out/
- Hybrid: https://www.protech.it.com/hybrid-attendance/

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

**How to Enroll a Student:**
1. Navigate to Students page (check user's role and provide correct link)
2. Click "Add Student" button
3. Fill in: LRN (12 digits), First Name, Middle Name (optional), Last Name, Grade, Section
4. Upload profile picture (optional)
5. Click "Save Student"
6. For face recognition, use "Face Enrollment" feature to capture student's face

**How to Face Enroll:**
1. Go to Face Enrollment page (Registrar role - provide link based on role)
2. Search and select the student
3. Allow camera access
4. Position student's face in the frame
5. Capture multiple face angles (system guides you)
6. Confirm enrollment

**How to Record Attendance:**
- **Automatic**: Students use Time In/Time Out pages (face recognition scans their face)
- **Manual**: Go to Attendance page, click "Add Record", select student, date, time in/out, status

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
            
            conversation_context += f"IMPORTANT: This user is a {user_role}. When providing navigation links:\n"
            
            # Provide role-specific URL examples
            if user_role == "Administrator":
                conversation_context += "USE THESE ADMIN URLs:\n"
                conversation_context += "- Students: https://www.protech.it.com/admin/students/\n"
                conversation_context += "- Attendance: https://www.protech.it.com/admin/attendance/\n"
                conversation_context += "- Users: https://www.protech.it.com/admin/users/\n"
                conversation_context += "- Messages: https://www.protech.it.com/admin/messages/\n"
            elif user_role == "Registrar":
                conversation_context += "USE THESE REGISTRAR URLs:\n"
                conversation_context += "- Students: https://www.protech.it.com/registrar/students/\n"
                conversation_context += "- Face Enrollment: https://www.protech.it.com/registrar/face-enroll/\n"
                conversation_context += "- Attendance: https://www.protech.it.com/registrar/attendance/\n"
                conversation_context += "- Messages: https://www.protech.it.com/registrar/messages/\n"
            elif user_role == "Principal":
                conversation_context += "USE THESE PRINCIPAL URLs:\n"
                conversation_context += "- Students: https://www.protech.it.com/principal/students/\n"
                conversation_context += "- Attendance: https://www.protech.it.com/principal/attendance/\n"
                conversation_context += "- Messages: https://www.protech.it.com/principal/messages/\n"
            elif "Teacher" in str(user_role):
                conversation_context += "USE THESE TEACHER URLs:\n"
                conversation_context += "- Students: https://www.protech.it.com/teacher/students/\n"
                conversation_context += "- Attendance: https://www.protech.it.com/teacher/attendance/\n"
                conversation_context += "- Messages: https://www.protech.it.com/teacher/messages/\n"
            
            conversation_context += "\nDO NOT use generic /admin/ or /registrar/ - use the URLs shown above for this specific role!\n"
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
