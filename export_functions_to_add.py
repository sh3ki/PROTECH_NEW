# Export functions to add to admin_views.py

# ==========================
#  EXPORT GRADES TO MULTIPLE FORMATS
# ==========================

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def export_grades(request):
    """Export grades to Excel, PDF, or Word file"""
    try:
        # Get export format (default to excel)
        export_format = request.GET.get('format', 'excel')
        
        # Get filter parameters
        search_query = request.GET.get('search', '').strip()
        
        # Get all grades
        from PROTECHAPP.models import Grade
        grades = Grade.objects.all().order_by('name')
        
        # Apply search filter
        if search_query:
            grades = grades.filter(name__icontains=search_query)
        
        # Define headers
        headers = ["ID", "Grade Name", "Total Sections", "Total Students", "Created Date"]
        
        # Prepare data rows
        data_rows = []
        for grade in grades:
            section_count = grade.section_set.count()
            student_count = Student.objects.filter(grade=grade).count()
            
            data_rows.append([
                str(grade.id),
                grade.name,
                str(section_count),
                str(student_count),
                grade.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(grade, 'created_at') and grade.created_at else ""
            ])
        
        # Export based on format
        if export_format == 'pdf':
            return export_grades_to_pdf(headers, data_rows)
        elif export_format == 'word':
            return export_grades_to_word(headers, data_rows)
        else:  # Default to Excel
            return export_grades_to_excel_format(headers, data_rows)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def export_grades_to_excel_format(headers, data_rows):
    """Export grades to Excel format"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Grades"
    
    # Define styles
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    border_style = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    center_alignment = Alignment(horizontal="center", vertical="center")
    left_alignment = Alignment(horizontal="left", vertical="center")
    
    # Set column widths
    column_widths = [8, 20, 18, 18, 20]
    for idx, width in enumerate(column_widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    
    # Add headers
    ws.append(headers)
    ws.row_dimensions[1].height = 25
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border_style
    
    # Add data rows
    for row_data in data_rows:
        ws.append(row_data)
    
    # Apply formatting to data rows
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = border_style
            
            # Center align ID, counts columns
            if col_idx in [1, 3, 4]:
                cell.alignment = center_alignment
            else:
                cell.alignment = left_alignment
    
    # Freeze header row
    ws.freeze_panes = ws['A2']
    
    # Save to buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    # Create HTTP response
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="grades_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    return response


def export_grades_to_pdf(headers, data_rows):
    """Export grades to PDF format"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Title
    elements.append(Paragraph("Grades Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Table data
    table_data = [headers] + data_rows
    
    # Create table
    table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1.5*inch])
    
    # Table style
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Total Grades: {len(data_rows)}", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="grades_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    return response


def export_grades_to_word(headers, data_rows):
    """Export grades to Word format"""
    doc = Document()
    
    # Add title
    title = doc.add_heading('Grades Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    # Create table
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    # Add headers
    header_cells = table.rows[0].cells
    for idx, header_text in enumerate(headers):
        cell = header_cells[idx]
        cell.text = header_text
        
        # Style header
        set_cell_background(cell, '1F4E78')
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(11)
                run.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add data rows
    for row_idx, row_data in enumerate(data_rows):
        row_cells = table.add_row().cells
        row_color = 'FFFFFF' if row_idx % 2 == 0 else 'F5F5F5'
        
        for idx, value in enumerate(row_data):
            cell = row_cells[idx]
            cell.text = str(value)
            set_cell_background(cell, row_color)
            
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                if idx in [0, 2, 3]:  # Center align ID and counts
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    # Add footer
    doc.add_paragraph()
    footer = doc.add_paragraph(f"Total Grades: {len(data_rows)}")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="grades_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx"'
    
    return response


# ==========================
#  EXPORT SECTIONS TO MULTIPLE FORMATS
# ==========================

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def export_sections(request):
    """Export sections to Excel, PDF, or Word file"""
    try:
        export_format = request.GET.get('format', 'excel')
        search_query = request.GET.get('search', '').strip()
        grade_filter = request.GET.get('grade', '').strip()
        advisor_filter = request.GET.get('advisor', '').strip()
        
        from PROTECHAPP.models import Section
        sections = Section.objects.select_related('grade', 'advisor').all().order_by('grade__name', 'name')
        
        if search_query:
            sections = sections.filter(
                Q(name__icontains=search_query) |
                Q(grade__name__icontains=search_query) |
                Q(advisor__first_name__icontains=search_query) |
                Q(advisor__last_name__icontains=search_query)
            )
        
        if grade_filter:
            sections = sections.filter(grade__id=grade_filter)
        
        if advisor_filter:
            if advisor_filter == 'with_advisor':
                sections = sections.filter(advisor__isnull=False)
            elif advisor_filter == 'without_advisor':
                sections = sections.filter(advisor__isnull=True)
        
        headers = ["ID", "Section Name", "Grade", "Advisor", "Total Students", "Created Date"]
        
        data_rows = []
        for section in sections:
            student_count = section.student_set.count()
            advisor_name = f"{section.advisor.first_name} {section.advisor.last_name}" if section.advisor else "No Advisor"
            
            data_rows.append([
                str(section.id),
                section.name,
                section.grade.name if section.grade else "",
                advisor_name,
                str(student_count),
                section.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(section, 'created_at') and section.created_at else ""
            ])
        
        if export_format == 'pdf':
            return export_sections_to_pdf(headers, data_rows)
        elif export_format == 'word':
            return export_sections_to_word(headers, data_rows)
        else:
            return export_sections_to_excel_format(headers, data_rows)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def export_sections_to_excel_format(headers, data_rows):
    """Export sections to Excel format"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Sections"
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    border_style = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    center_alignment = Alignment(horizontal="center", vertical="center")
    left_alignment = Alignment(horizontal="left", vertical="center")
    
    column_widths = [8, 20, 15, 25, 18, 20]
    for idx, width in enumerate(column_widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    
    ws.append(headers)
    ws.row_dimensions[1].height = 25
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border_style
    
    for row_data in data_rows:
        ws.append(row_data)
    
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = border_style
            
            if col_idx in [1, 5]:  # ID and Total Students
                cell.alignment = center_alignment
            else:
                cell.alignment = left_alignment
    
    ws.freeze_panes = ws['A2']
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="sections_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    return response


def export_sections_to_pdf(headers, data_rows):
    """Export sections to PDF format"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("Sections Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    table_data = [headers] + data_rows
    table = Table(table_data, colWidths=[0.4*inch, 1.2*inch, 0.8*inch, 1.5*inch, 1*inch, 1.2*inch])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Total Sections: {len(data_rows)}", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sections_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    return response


def export_sections_to_word(headers, data_rows):
    """Export sections to Word format"""
    doc = Document()
    
    title = doc.add_heading('Sections Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
    
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    header_cells = table.rows[0].cells
    for idx, header_text in enumerate(headers):
        cell = header_cells[idx]
        cell.text = header_text
        set_cell_background(cell, '1F4E78')
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(11)
                run.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    for row_idx, row_data in enumerate(data_rows):
        row_cells = table.add_row().cells
        row_color = 'FFFFFF' if row_idx % 2 == 0 else 'F5F5F5'
        
        for idx, value in enumerate(row_data):
            cell = row_cells[idx]
            cell.text = str(value)
            set_cell_background(cell, row_color)
            
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                if idx in [0, 4]:  # ID and Total Students
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    doc.add_paragraph()
    footer = doc.add_paragraph(f"Total Sections: {len(data_rows)}")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="sections_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx"'
    
    return response


# ==========================
#  EXPORT GUARDIANS TO MULTIPLE FORMATS
# ==========================

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def export_guardians(request):
    """Export guardians to Excel, PDF, or Word file"""
    try:
        export_format = request.GET.get('format', 'excel')
        search_query = request.GET.get('search', '').strip()
        relationship_filter = request.GET.get('relationship', '').strip()
        grade_filter = request.GET.get('grade', '').strip()
        section_filter = request.GET.get('section', '').strip()
        
        from PROTECHAPP.models import Guardian
        guardians = Guardian.objects.prefetch_related('students').all().order_by('last_name', 'first_name')
        
        if search_query:
            guardians = guardians.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        if relationship_filter:
            guardians = guardians.filter(relationship=relationship_filter)
        
        if grade_filter:
            guardians = guardians.filter(students__grade__id=grade_filter).distinct()
        
        if section_filter:
            guardians = guardians.filter(students__section__id=section_filter).distinct()
        
        headers = ["ID", "Guardian Name", "Email", "Phone", "Relationship", "Total Children", "Created Date"]
        
        data_rows = []
        for guardian in guardians:
            children_count = guardian.students.count()
            full_name = f"{guardian.first_name} {guardian.last_name}"
            
            data_rows.append([
                str(guardian.id),
                full_name,
                guardian.email or "",
                guardian.phone or "",
                guardian.get_relationship_display() if hasattr(guardian, 'get_relationship_display') else guardian.relationship,
                str(children_count),
                guardian.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(guardian, 'created_at') and guardian.created_at else ""
            ])
        
        if export_format == 'pdf':
            return export_guardians_to_pdf(headers, data_rows)
        elif export_format == 'word':
            return export_guardians_to_word(headers, data_rows)
        else:
            return export_guardians_to_excel_format(headers, data_rows)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def export_guardians_to_excel_format(headers, data_rows):
    """Export guardians to Excel format"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Guardians"
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    border_style = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    center_alignment = Alignment(horizontal="center", vertical="center")
    left_alignment = Alignment(horizontal="left", vertical="center")
    
    column_widths = [8, 25, 30, 18, 18, 18, 20]
    for idx, width in enumerate(column_widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    
    ws.append(headers)
    ws.row_dimensions[1].height = 25
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border_style
    
    for row_data in data_rows:
        ws.append(row_data)
    
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = border_style
            
            if col_idx in [1, 6]:  # ID and Total Children
                cell.alignment = center_alignment
            else:
                cell.alignment = left_alignment
    
    ws.freeze_panes = ws['A2']
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="guardians_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    return response


def export_guardians_to_pdf(headers, data_rows):
    """Export guardians to PDF format"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("Guardians Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    table_data = [headers] + data_rows
    table = Table(table_data, colWidths=[0.3*inch, 1.5*inch, 1.5*inch, 1*inch, 1*inch, 0.7*inch, 1.1*inch])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Total Guardians: {len(data_rows)}", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="guardians_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    return response


def export_guardians_to_word(headers, data_rows):
    """Export guardians to Word format"""
    doc = Document()
    
    title = doc.add_heading('Guardians Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
    
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    header_cells = table.rows[0].cells
    for idx, header_text in enumerate(headers):
        cell = header_cells[idx]
        cell.text = header_text
        set_cell_background(cell, '1F4E78')
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(11)
                run.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    for row_idx, row_data in enumerate(data_rows):
        row_cells = table.add_row().cells
        row_color = 'FFFFFF' if row_idx % 2 == 0 else 'F5F5F5'
        
        for idx, value in enumerate(row_data):
            cell = row_cells[idx]
            cell.text = str(value)
            set_cell_background(cell, row_color)
            
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                if idx in [0, 5]:  # ID and Total Children
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    doc.add_paragraph()
    footer = doc.add_paragraph(f"Total Guardians: {len(data_rows)}")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="guardians_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx"'
    
    return response


# ==========================
#  EXPORT EXCUSED ABSENCES TO MULTIPLE FORMATS
# ==========================

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def export_excused(request):
    """Export excused absences to Excel, PDF, or Word file"""
    try:
        export_format = request.GET.get('format', 'excel')
        search_query = request.GET.get('search', '').strip()
        grade_filter = request.GET.get('grade', '').strip()
        section_filter = request.GET.get('section', '').strip()
        status_filter = request.GET.get('status', '').strip()
        date_filter = request.GET.get('date', '').strip()
        
        from PROTECHAPP.models import ExcusedAbsence
        from django.utils import timezone
        
        excused = ExcusedAbsence.objects.select_related('student', 'student__grade', 'student__section').all().order_by('-date_absent')
        
        if search_query:
            excused = excused.filter(
                Q(student__first_name__icontains=search_query) |
                Q(student__last_name__icontains=search_query) |
                Q(student__lrn__icontains=search_query) |
                Q(student__section__name__icontains=search_query)
            )
        
        if grade_filter:
            excused = excused.filter(student__grade__id=grade_filter)
        
        if section_filter:
            excused = excused.filter(student__section__id=section_filter)
        
        if status_filter:
            today = timezone.now().date()
            if status_filter == 'ACTIVE':
                excused = excused.filter(date_absent__lte=today, return_date__gte=today)
            elif status_filter == 'UPCOMING':
                excused = excused.filter(date_absent__gt=today)
            elif status_filter == 'EXPIRED':
                excused = excused.filter(return_date__lt=today)
        
        if date_filter:
            excused = excused.filter(date_absent=date_filter)
        
        headers = ["ID", "Student Name", "LRN", "Grade", "Section", "Date Absent", "Return Date", "Reason", "Has Letter"]
        
        data_rows = []
        for record in excused:
            student_name = f"{record.student.first_name} {record.student.last_name}"
            has_letter = "Yes" if record.excuse_letter else "No"
            
            data_rows.append([
                str(record.id),
                student_name,
                record.student.lrn or "",
                record.student.grade.name if record.student.grade else "",
                record.student.section.name if record.student.section else "",
                record.date_absent.strftime("%Y-%m-%d") if record.date_absent else "",
                record.return_date.strftime("%Y-%m-%d") if record.return_date else "",
                record.reason or "",
                has_letter
            ])
        
        if export_format == 'pdf':
            return export_excused_to_pdf(headers, data_rows)
        elif export_format == 'word':
            return export_excused_to_word(headers, data_rows)
        else:
            return export_excused_to_excel_format(headers, data_rows)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def export_excused_to_excel_format(headers, data_rows):
    """Export excused absences to Excel format"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Excused Absences"
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    border_style = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    center_alignment = Alignment(horizontal="center", vertical="center")
    left_alignment = Alignment(horizontal="left", vertical="center")
    
    column_widths = [8, 25, 15, 12, 15, 15, 15, 35, 12]
    for idx, width in enumerate(column_widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width
    
    ws.append(headers)
    ws.row_dimensions[1].height = 25
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border_style
    
    for row_data in data_rows:
        ws.append(row_data)
    
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = border_style
            
            if col_idx in [1, 9]:  # ID and Has Letter
                cell.alignment = center_alignment
            else:
                cell.alignment = left_alignment
    
    ws.freeze_panes = ws['A2']
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="excused_absences_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    return response


def export_excused_to_pdf(headers, data_rows):
    """Export excused absences to PDF format"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=30,
        alignment=1
    )
    
    elements.append(Paragraph("Excused Absences Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    table_data = [headers] + data_rows
    table = Table(table_data, colWidths=[0.4*inch, 1.5*inch, 0.9*inch, 0.7*inch, 0.9*inch, 1*inch, 1*inch, 2*inch, 0.7*inch])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Total Excused Absences: {len(data_rows)}", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="excused_absences_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    return response


def export_excused_to_word(headers, data_rows):
    """Export excused absences to Word format"""
    doc = Document()
    
    title = doc.add_heading('Excused Absences Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
    
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    header_cells = table.rows[0].cells
    for idx, header_text in enumerate(headers):
        cell = header_cells[idx]
        cell.text = header_text
        set_cell_background(cell, '1F4E78')
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(11)
                run.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    for row_idx, row_data in enumerate(data_rows):
        row_cells = table.add_row().cells
        row_color = 'FFFFFF' if row_idx % 2 == 0 else 'F5F5F5'
        
        for idx, value in enumerate(row_data):
            cell = row_cells[idx]
            cell.text = str(value)
            set_cell_background(cell, row_color)
            
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                if idx in [0, 8]:  # ID and Has Letter
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    doc.add_paragraph()
    footer = doc.add_paragraph(f"Total Excused Absences: {len(data_rows)}")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="excused_absences_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx"'
    
    return response
