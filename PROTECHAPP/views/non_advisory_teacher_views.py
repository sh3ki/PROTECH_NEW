from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from PROTECHAPP.models import CustomUser, Student, Attendance, Guardian, UserRole
import io
from datetime import datetime

def is_teacher(user):
    """Check if the logged-in user is a teacher"""
    return user.is_authenticated and user.role == UserRole.TEACHER

@login_required
@user_passes_test(is_teacher)
def teacher_non_advisory_dashboard(request):
    """View for teacher dashboard"""
    # Retrieve today's date for the dashboard
    current_date = timezone.now()
    
    # Example data that might be needed for a teacher's dashboard
    today_attendance_percentage = 96  # This would come from a database query
    
    context = {
        'current_date': current_date,
        'today_attendance_percentage': today_attendance_percentage
    }
    
    return render(request, 'teacher/non_advisory/dashboard.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_non_advisory_students(request):
    """View for students listing"""
    students = Student.objects.all()
    context = {
        'students': students
    }
    return render(request, 'teacher/non_advisory/students.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_non_advisory_guardians(request):
    """View for guardians listing"""
    guardians = Guardian.objects.all()
    context = {
        'guardians': guardians
    }
    return render(request, 'teacher/non_advisory/guardians.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_non_advisory_attendance(request):
    """View for attendance records"""
    today = timezone.now().date()
    attendance_records = Attendance.objects.filter(date=today)
    context = {
        'attendance_records': attendance_records
    }
    return render(request, 'teacher/non_advisory/attendance.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_non_advisory_excused(request):
    """View for excused absences"""
    return render(request, 'teacher/non_advisory/excused.html')

@login_required
@user_passes_test(is_teacher)
def teacher_non_advisory_messages(request):
    """View for messages - now using PostgreSQL with polling"""
    return render(request, 'teacher/non_advisory/messages.html')

@login_required
@user_passes_test(is_teacher)
def teacher_non_advisory_settings(request):
    """View for settings"""
    return render(request, 'teacher/non_advisory/settings.html')

# Export Functions
@login_required
@user_passes_test(is_teacher)
def export_non_advisory_students(request):
    """Export all students to Excel, PDF, or Word"""
    try:
        import pandas as pd
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from docx import Document
        from docx.shared import Inches, RGBColor, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as e:
        return JsonResponse({'success': False, 'error': f'Required library not installed: {str(e)}'}, status=500)
    
    export_format = request.GET.get('format', 'excel')
    students = Student.objects.all().select_related('grade', 'section').order_by('id')
    
    headers = ['ID', 'LRN', 'First Name', 'Middle Name', 'Last Name', 'Email', 'Grade', 'Section', 'Status', 'Face Enrolled']
    data_rows = []
    
    for student in students:
        data_rows.append([
            student.id,
            student.lrn or '',
            student.first_name,
            student.middle_name or '',
            student.last_name,
            student.email or '',
            student.grade.name if student.grade else '',
            student.section.name if student.section else '',
            student.status,
            'Yes' if student.face_path else 'No'
        ])
    
    if export_format == 'pdf':
        return export_teacher_data_to_pdf(headers, data_rows, "All Students")
    elif export_format == 'word':
        return export_teacher_data_to_word(headers, data_rows, "All Students")
    else:
        return export_teacher_data_to_excel(headers, data_rows, "All Students")

@login_required
@user_passes_test(is_teacher)
def export_non_advisory_guardians(request):
    """Export all guardians to Excel, PDF, or Word"""
    try:
        import pandas as pd
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from docx import Document
        from docx.shared import Inches, RGBColor, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as e:
        return JsonResponse({'success': False, 'error': f'Required library not installed: {str(e)}'}, status=500)
    
    export_format = request.GET.get('format', 'excel')
    guardians = Guardian.objects.all().select_related('student').order_by('id')
    
    headers = ['ID', 'First Name', 'Middle Name', 'Last Name', 'Relationship', 'Contact Number', 'Email', 'Student Name']
    data_rows = []
    
    for guardian in guardians:
        data_rows.append([
            guardian.id,
            guardian.first_name,
            guardian.middle_name or '',
            guardian.last_name,
            guardian.relationship or '',
            guardian.contact_number or '',
            guardian.email or '',
            f"{guardian.student.first_name} {guardian.student.last_name}" if guardian.student else ''
        ])
    
    if export_format == 'pdf':
        return export_teacher_data_to_pdf(headers, data_rows, "All Guardians")
    elif export_format == 'word':
        return export_teacher_data_to_word(headers, data_rows, "All Guardians")
    else:
        return export_teacher_data_to_excel(headers, data_rows, "All Guardians")

def export_teacher_data_to_excel(headers, data_rows, title):
    """Export data to Excel format"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]  # Excel sheet name limit
    
    # Write headers
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
    
    # Write data rows
    for row_num, row_data in enumerate(data_rows, 2):
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='left', vertical='center')
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column = [cell for cell in column]
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[get_column_letter(column[0].column)].width = adjusted_width
    
    # Save to HTTP response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{title}.xlsx"'
    wb.save(response)
    return response

def export_teacher_data_to_pdf(headers, data_rows, title):
    """Export data to PDF format"""
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = styles['Heading1']
    title_style.textColor = colors.HexColor('#1F4E78')
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Table
    table_data = [headers] + data_rows
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{title}.pdf"'
    return response

def export_teacher_data_to_word(headers, data_rows, title):
    """Export data to Word format"""
    from docx import Document
    from docx.shared import Inches, RGBColor, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    doc = Document()
    
    # Title
    heading = doc.add_heading(title, 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.runs[0].font.color.rgb = RGBColor(31, 78, 120)
    
    # Table
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    # Headers
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        hdr_cells[i].paragraphs[0].runs[0].font.bold = True
        hdr_cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(31, 78, 120)
    
    # Data rows
    for row_data in data_rows:
        row_cells = table.add_row().cells
        for i, value in enumerate(row_data):
            row_cells[i].text = str(value)
    
    # Save to buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{title}.docx"'
    return response
