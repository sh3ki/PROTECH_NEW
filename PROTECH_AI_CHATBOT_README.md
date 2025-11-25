# PROTECH AI Chatbot - Implementation Guide

## Overview
The PROTECH AI Chatbot is an intelligent virtual assistant integrated into the PROTECH Face Recognition Attendance Monitoring System. It provides real-time help, answers questions, and guides users through the system's features.

## Features

### ✨ Key Capabilities
- **Intelligent Q&A**: Answers questions about system features, navigation, and procedures
- **Context-Aware**: Maintains conversation history for contextual responses
- **Multi-Topic Support**: Can answer both system-specific and general questions
- **User-Friendly Interface**: Clean, modern chat interface that matches the PROTECH design
- **Real-Time Responses**: Powered by OpenAI GPT-3.5 Turbo
- **Session-Based**: Maintains chat history during the session
- **Dark Mode Support**: Automatically adapts to the system's light/dark theme
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Implementation Details

### 🔧 Components

#### 1. Backend (`chatbot_views.py`)
- **Location**: `PROTECHAPP/views/chatbot_views.py`
- **Endpoint**: `/api/chatbot/message/`
- **Method**: POST
- **Functionality**:
  - Processes user messages
  - Maintains conversation history
  - Communicates with OpenAI API
  - Implements fallback API key for redundancy
  - Returns AI-generated responses

#### 2. Frontend Widget (`chatbot_widget.html`)
- **Location**: `templates/components/chatbot_widget.html`
- **Features**:
  - Floating chat button (bottom-right)
  - Expandable chat window
  - Message history display
  - Typing indicators
  - Smooth animations
  - Auto-scroll to latest messages

#### 3. Integration
- **Base Template**: Included in `templates/components/base_component.html`
- **Excluded Pages**: Time In, Time Out, Hybrid Attendance, Select Device
- **Available On**: All dashboard pages (Admin, Registrar, Principal, Teacher)

### 🔑 Configuration

#### Environment Variables (.env)
```env
# Primary OpenAI API Key
OPENAI_API_KEY=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

# Fallback OpenAI API Key (used if primary fails)
OPENAI_API_KEY_FALLBACK=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
```

#### Dependencies
Added to `requirements.txt`:
```
openai>=0.28.0
```

### 🎯 System Knowledge

The chatbot is trained with comprehensive knowledge about:

#### User Roles
- **Administrator**: Full system control, user management, settings
- **Principal**: School oversight, reporting, analytics
- **Registrar**: Student enrollment, face enrollment, records
- **Teacher (Advisory)**: Class-specific attendance and student management
- **Teacher (Non-Advisory)**: View-only access to students and attendance

#### Features
- Face Recognition Attendance (Time In/Out, Hybrid Mode)
- Student Management (Add, Edit, Import/Export)
- Guardian Management
- Attendance Records
- Excused Absences
- Messaging System
- Grades & Sections
- Reports & Analytics

#### Common Procedures
- How to enroll students
- How to use face enrollment
- How to record attendance
- How to approve excused absences
- Navigation paths for all features
- Import/Export procedures

## Usage

### For End Users

#### Opening the Chatbot
1. Look for the blue circular button with an AI icon at the bottom-right corner
2. Click the button to open the chat window
3. Type your question in the input field
4. Press Enter or click the send button

#### Sample Questions
- "How do I add a new student?"
- "Where can I see attendance records?"
- "How does face recognition work?"
- "What's the difference between admin and registrar?"
- "How to approve an excused absence?"
- "Where are the import/export features?"
- "How do I enroll a student's face?"

#### Best Practices
- Ask clear, specific questions
- Provide context if needed
- Be patient while the AI generates responses
- The chatbot remembers your conversation history
- You can ask follow-up questions

### For Developers

#### API Request Format
```json
POST /api/chatbot/message/
{
    "message": "How do I add a student?",
    "history": [
        {
            "role": "user",
            "content": "Previous user message"
        },
        {
            "role": "assistant",
            "content": "Previous bot response"
        }
    ]
}
```

#### API Response Format
```json
{
    "success": true,
    "message": "AI-generated response text",
    "timestamp": "2025-11-24T12:34:56.789Z"
}
```

#### Error Handling
- Primary API key failures automatically switch to fallback key
- Network errors display user-friendly messages
- Invalid requests return 400 status with error details
- Service unavailable returns 503 status

## Customization

### Modifying the System Prompt
Edit the `SYSTEM_PROMPT` in `chatbot_views.py` to:
- Add new features or procedures
- Update navigation paths
- Change the chatbot's personality
- Add domain-specific knowledge

### Styling
Modify `chatbot_widget.html` to:
- Change colors (currently matches PROTECH blue theme)
- Adjust sizes and positioning
- Modify animations
- Update icons

### Behavior
Adjust in `chatbot_views.py`:
- `model`: Change AI model (default: gpt-3.5-turbo)
- `max_tokens`: Adjust response length (default: 500)
- `temperature`: Control creativity (default: 0.7)
- Conversation history limit (default: last 10 messages)

## Troubleshooting

### Chatbot Not Appearing
1. Check that the page extends `base_component.html`
2. Verify it's not an excluded page (time-in, time-out, hybrid, select-device)
3. Clear browser cache and reload

### API Errors
1. Verify OpenAI API keys in `.env` file
2. Check API key validity and quota
3. Review server logs for detailed error messages
4. Ensure `openai` package is installed

### Slow Responses
1. Check internet connection
2. Verify OpenAI service status
3. Consider reducing `max_tokens` for faster responses
4. Check for API rate limits

### Conversation Not Maintaining Context
1. Ensure JavaScript console has no errors
2. Check that conversation history is being sent in requests
3. Verify session storage is enabled in browser

## Security Considerations

### API Key Protection
- ✅ API keys stored in `.env` (not committed to Git)
- ✅ Keys loaded via environment variables
- ✅ Never exposed to frontend/client-side code

### Input Validation
- ✅ User messages are validated and sanitized
- ✅ HTML escaping prevents XSS attacks
- ✅ CSRF protection on API endpoint

### Rate Limiting
Consider implementing:
- Request rate limiting per user
- Message length restrictions
- Conversation history size limits

## Maintenance

### Updating System Knowledge
When system features change:
1. Update `SYSTEM_PROMPT` in `chatbot_views.py`
2. Add new features, procedures, or navigation paths
3. Test with sample questions

### Monitoring
Track:
- API usage and costs
- Response times
- Error rates
- User feedback

### Backup API Keys
- Keep fallback key updated
- Monitor both keys' usage limits
- Set up alerts for quota warnings

## Future Enhancements

### Potential Features
- [ ] Message rating system (helpful/not helpful)
- [ ] Suggested questions based on current page
- [ ] Voice input support
- [ ] File/image upload for visual questions
- [ ] Multi-language support
- [ ] Analytics dashboard for chatbot usage
- [ ] Integration with system notifications
- [ ] Personalized responses based on user role

### Performance Improvements
- [ ] Implement caching for common questions
- [ ] Add response streaming for faster perceived performance
- [ ] Optimize conversation history management
- [ ] Implement request queuing

## Support

For issues or questions:
1. Check this documentation
2. Review error logs in Django admin
3. Test API endpoints directly
4. Contact system administrator

## Credits

- **AI Model**: OpenAI GPT-3.5 Turbo
- **Framework**: Django 5.2.6
- **Frontend**: Tailwind CSS
- **Integration**: Custom implementation

---

**Version**: 1.0  
**Last Updated**: November 24, 2025  
**Author**: PROTECH Development Team
