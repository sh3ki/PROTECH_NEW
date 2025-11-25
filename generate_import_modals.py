"""
Script to generate consistent import modals matching the Students page design.
This script generates the complete HTML for import modals for all admin pages.
"""

MODAL_CONFIGS = {
    'users': {
        'title': 'Users',
        'subtitle': 'Upload Excel file with user data',
        'template_url': 'download_users_import_template',
        'columns': [
            {'name': 'ID', 'required': False, 'description': 'User ID (optional, for reference only)', 'example': 'Leave blank for new users'},
            {'name': 'Username', 'required': True, 'description': 'Unique username', 'example': 'john.doe'},
            {'name': 'Email', 'required': True, 'description': 'Email address', 'example': 'john.doe@school.edu'},
            {'name': 'First Name', 'required': True, 'description': 'User first name', 'example': 'John'},
            {'name': 'Last Name', 'required': True, 'description': 'User last name', 'example': 'Doe'},
            {'name': 'Middle Name', 'required': False, 'description': 'User middle name', 'example': 'Smith'},
            {'name': 'Role', 'required': True, 'description': 'User role', 'example': 'Teacher, Admin, Principal, Registrar'},
            {'name': 'Status', 'required': False, 'description': 'Active status', 'example': 'Active, Inactive'},
            {'name': 'Password', 'required': True, 'description': 'Initial password (min 8 chars)', 'example': 'temp123456'},
        ],
        'excel_preview': [
            ['1', 'john.doe', 'john.doe@school.edu', 'John', 'Doe', 'Smith', 'Teacher', 'Active', 'temp123456'],
            ['2', 'jane.smith', 'jane.smith@school.edu', 'Jane', 'Smith', '', 'Principal', 'Active', 'temp123456'],
            ['3', 'admin.user', 'admin@school.edu', 'Admin', 'User', '', 'Admin', 'Active', 'admin123456'],
        ],
        'pro_tips': [
            '<strong>Leave ID blank</strong> for new users (ID is auto-generated)',
            'Username and email must be unique across the system',
            '<strong>Password is required</strong> for new users (minimum 8 characters)',
            'Valid roles: ADMIN, TEACHER, PRINCIPAL, REGISTRAR',
        ],
        'important_notes': [
            '<strong>Existing Records:</strong> If the ID column contains an existing user ID, that row will be skipped to prevent duplicates.',
            '<strong>Username:</strong> Must be unique. Existing usernames will be updated.',
            '<strong>Email:</strong> Must be unique across all users.',
            '<strong>Password:</strong> Required for new users. Must be at least 8 characters.',
            '<strong>Role:</strong> Must be one of: ADMIN, TEACHER, PRINCIPAL, REGISTRAR.',
        ],
    },
    'teachers': {
        'title': 'Teachers',
        'subtitle': 'Upload Excel file with teacher data',
        'template_url': 'download_teachers_import_template',
        'columns': [
            {'name': 'ID', 'required': False, 'description': 'Teacher ID (optional, for reference only)', 'example': 'Leave blank for new teachers'},
            {'name': 'First Name', 'required': True, 'description': 'Teacher first name', 'example': 'John'},
            {'name': 'Middle Name', 'required': False, 'description': 'Teacher middle name', 'example': 'Smith'},
            {'name': 'Last Name', 'required': True, 'description': 'Teacher last name', 'example': 'Doe'},
            {'name': 'Username', 'required': True, 'description': 'Unique username', 'example': 'john.doe'},
            {'name': 'Email', 'required': True, 'description': 'Email address', 'example': 'john.doe@school.edu'},
            {'name': 'Password', 'required': False, 'description': 'Auto-generated for new teachers', 'example': 'Leave blank (system generated)'},
        ],
        'excel_preview': [
            ['1', 'John', 'Smith', 'Doe', 'john.doe', 'john.doe@school.edu', 'auto-generated'],
            ['2', 'Jane', '', 'Smith', 'jane.smith', 'jane.smith@school.edu', 'auto-generated'],
            ['3', 'Maria', 'Cruz', 'Santos', 'maria.santos', 'maria.santos@school.edu', 'auto-generated'],
        ],
        'pro_tips': [
            '<strong>Leave ID blank</strong> for new teachers (ID is auto-generated)',
            '<strong>Passwords are auto-generated</strong> and sent to teachers\' email addresses',
            'Username and email must be unique across the system',
            'Middle Name is optional, other fields are required',
        ],
        'important_notes': [
            '<strong>Existing Records:</strong> If the ID column contains an existing teacher ID, that row will be skipped.',
            '<strong>Passwords:</strong> Automatically generated and sent to the teacher\'s email address.',
            '<strong>Username/Email:</strong> Must be unique across the system.',
        ],
    },
    'grades': {
        'title': 'Grades',
        'subtitle': 'Upload Excel file with grade data',
        'template_url': 'download_grades_import_template',
        'columns': [
            {'name': 'ID', 'required': False, 'description': 'Grade ID (optional, for reference only)', 'example': 'Leave blank for new grades'},
            {'name': 'Grade Name', 'required': True, 'description': 'Grade name', 'example': 'Grade 7, Grade 8, Grade 9'},
        ],
        'excel_preview': [
            ['1', 'Grade 7'],
            ['2', 'Grade 8'],
            ['3', 'Grade 9'],
            ['4', 'Grade 10'],
        ],
        'pro_tips': [
            '<strong>Leave ID blank</strong> for new grades (ID is auto-generated)',
            '<strong>Grade names must be unique</strong> - duplicate names will be rejected',
            'Use consistent naming format (e.g., "Grade 7", "Grade 8")',
        ],
        'important_notes': [
            '<strong>Existing Records:</strong> Rows with existing IDs will be skipped (not imported).',
            '<strong>Unique Names:</strong> Grade names must be unique.',
        ],
    },
    'sections': {
        'title': 'Sections',
        'subtitle': 'Upload Excel file with section data',
        'template_url': 'download_sections_import_template',
        'columns': [
            {'name': 'ID', 'required': False, 'description': 'Section ID (optional, for reference only)', 'example': 'Leave blank for new sections'},
            {'name': 'Section Name', 'required': True, 'description': 'Section name', 'example': 'Section A, Section B'},
            {'name': 'Grade', 'required': True, 'description': 'Grade name (must exist)', 'example': 'Grade 7'},
            {'name': 'Room Number', 'required': False, 'description': 'Classroom number', 'example': '101, 102'},
            {'name': 'Capacity', 'required': False, 'description': 'Maximum students', 'example': '40'},
        ],
        'excel_preview': [
            ['1', 'Section A', 'Grade 7', '101', '40'],
            ['2', 'Section B', 'Grade 7', '102', '40'],
            ['3', 'Section A', 'Grade 8', '201', '35'],
        ],
        'pro_tips': [
            '<strong>Leave ID blank</strong> for new sections (ID is auto-generated)',
            '<strong>Grade must exist</strong> in the system before importing sections',
            'Room Number and Capacity are optional fields',
        ],
        'important_notes': [
            '<strong>Grade Validation:</strong> The grade must already exist in the system.',
            '<strong>Combination Uniqueness:</strong> Section name + Grade combination must be unique.',
        ],
    },
    'guardians': {
        'title': 'Guardians',
        'subtitle': 'Upload Excel file with guardian data',
        'template_url': 'download_guardians_import_template',
        'columns': [
            {'name': 'ID', 'required': False, 'description': 'Guardian ID (optional, for reference only)', 'example': 'Leave blank for new guardians'},
            {'name': 'First Name', 'required': True, 'description': 'Guardian first name', 'example': 'John'},
            {'name': 'Middle Name', 'required': False, 'description': 'Guardian middle name', 'example': 'Smith'},
            {'name': 'Last Name', 'required': True, 'description': 'Guardian last name', 'example': 'Doe'},
            {'name': 'Relationship', 'required': True, 'description': 'Relationship to student', 'example': 'FATHER, MOTHER, GUARDIAN'},
            {'name': 'Contact Number', 'required': True, 'description': 'Phone number', 'example': '09123456789'},
            {'name': 'Email', 'required': False, 'description': 'Email address', 'example': 'john.doe@email.com'},
            {'name': 'Student Name', 'required': True, 'description': 'Student full name (must exist)', 'example': 'Jane Doe'},
        ],
        'excel_preview': [
            ['1', 'John', 'Smith', 'Doe', 'FATHER', '09123456789', 'john.doe@email.com', 'Jane Doe'],
            ['2', 'Maria', 'Cruz', 'Santos', 'MOTHER', '09187654321', 'maria.santos@email.com', 'Pedro Santos'],
            ['3', 'Robert', '', 'Garcia', 'GUARDIAN', '09198765432', '', 'Anna Garcia'],
        ],
        'pro_tips': [
            '<strong>Leave ID blank</strong> for new guardians (ID is auto-generated)',
            '<strong>Valid relationships:</strong> FATHER, MOTHER, GUARDIAN, GRANDMOTHER, GRANDFATHER, AUNT, UNCLE, SIBLING, OTHER',
            'Student must exist in the system (matched by full name)',
            'Email is optional, Middle Name is optional',
        ],
        'important_notes': [
            '<strong>Student Validation:</strong> Student must exist in the system.',
            '<strong>Relationship Types:</strong> FATHER, MOTHER, GUARDIAN, GRANDMOTHER, GRANDFATHER, AUNT, UNCLE, SIBLING, OTHER.',
            '<strong>Contact Number:</strong> Required field for all guardians.',
        ],
    },
    'attendance': {
        'title': 'Attendance Records',
        'subtitle': 'Upload Excel file with attendance data',
        'template_url': 'download_attendance_import_template',
        'columns': [
            {'name': 'ID', 'required': False, 'description': 'Attendance ID (optional)', 'example': 'Leave blank for new records'},
            {'name': 'Student LRN', 'required': True, 'description': 'Student LRN (12 digits)', 'example': '123456789012'},
            {'name': 'Date', 'required': True, 'description': 'Attendance date', 'example': '2025-11-23'},
            {'name': 'Time In', 'required': False, 'description': 'Check-in time', 'example': '07:30:00'},
            {'name': 'Time Out', 'required': False, 'description': 'Check-out time', 'example': '17:00:00'},
            {'name': 'Status', 'required': True, 'description': 'Attendance status', 'example': 'ON TIME, LATE, ABSENT, EXCUSED'},
        ],
        'excel_preview': [
            ['1', '123456789012', '2025-11-23', '07:30:00', '17:00:00', 'ON TIME'],
            ['2', '123456789013', '2025-11-23', '07:45:00', '17:00:00', 'LATE'],
            ['3', '123456789014', '2025-11-23', '', '', 'ABSENT'],
        ],
        'pro_tips': [
            '<strong>Leave ID blank</strong> for new records (ID is auto-generated)',
            '<strong>Student LRN must be exactly 12 digits</strong> and must exist in the system',
            '<strong>Valid statuses:</strong> ON TIME, LATE, ABSENT, EXCUSED',
            'Date format: YYYY-MM-DD, Time format: HH:MM:SS',
        ],
        'important_notes': [
            '<strong>LRN Validation:</strong> Student with the LRN must exist in the system.',
            '<strong>Date Format:</strong> Use YYYY-MM-DD format (e.g., 2025-11-23).',
            '<strong>Status Values:</strong> ON TIME, LATE, ABSENT, or EXCUSED.',
        ],
    },
    'excused': {
        'title': 'Excuse Letters',
        'subtitle': 'Upload Excel file with excuse letter data',
        'template_url': 'download_excused_import_template',
        'columns': [
            {'name': 'ID', 'required': False, 'description': 'Excuse ID (optional)', 'example': 'Leave blank for new excuses'},
            {'name': 'Student LRN', 'required': True, 'description': 'Student LRN (12 digits)', 'example': '123456789012'},
            {'name': 'Date', 'required': True, 'description': 'Excuse date', 'example': '2025-11-23'},
            {'name': 'Reason', 'required': True, 'description': 'Reason for excuse', 'example': 'Medical appointment'},
            {'name': 'Status', 'required': True, 'description': 'Approval status', 'example': 'PENDING, APPROVED, REJECTED'},
        ],
        'excel_preview': [
            ['1', '123456789012', '2025-11-23', 'Medical appointment', 'APPROVED'],
            ['2', '123456789013', '2025-11-23', 'Family emergency', 'PENDING'],
            ['3', '123456789014', '2025-11-22', 'Sick', 'APPROVED'],
        ],
        'pro_tips': [
            '<strong>Leave ID blank</strong> for new excuse letters (ID is auto-generated)',
            '<strong>Student LRN must be exactly 12 digits</strong> and must exist in the system',
            '<strong>Valid statuses:</strong> PENDING, APPROVED, REJECTED',
            'Reason should be a clear description of why the student was absent',
        ],
        'important_notes': [
            '<strong>LRN Validation:</strong> Student with the LRN must exist in the system.',
            '<strong>Date Format:</strong> Use YYYY-MM-DD format (e.g., 2025-11-23).',
            '<strong>Status Values:</strong> PENDING, APPROVED, or REJECTED.',
        ],
    },
}

def generate_modal_html(config_key):
    """Generate the complete modal HTML for a given configuration."""
    config = MODAL_CONFIGS[config_key]
    entity = config_key.lower()
    
    # Generate column headers for Excel preview
    excel_headers = ''.join([
        f'<th class="border border-gray-300 dark:border-gray-600 px-2 py-2 text-white font-bold text-center" style="min-width: 40px;">{col["name"]}</th>'
        if col["name"] == "ID" else
        f'<th class="border border-gray-300 dark:border-gray-600 px-2 py-2 text-white font-bold" style="min-width: {len(col["name"]) * 10 + 60}px;">{col["name"]}</th>'
        for col in config['columns']
    ])
    
    # Generate Excel preview rows
    excel_rows = ''
    for idx, row_data in enumerate(config['excel_preview']):
        bg_class = 'bg-white dark:bg-gray-700' if idx % 2 == 0 else 'bg-gray-50 dark:bg-gray-750'
        cells = ''.join([
            f'<td class="border border-gray-300 dark:border-gray-600 px-2 py-1.5 text-center text-gray-400">{cell}</td>'
            if i == 0 else
            f'<td class="border border-gray-300 dark:border-gray-600 px-2 py-1.5 {"text-gray-400 italic" if cell in ["auto-generated", ""] else ""}">{cell}</td>'
            for i, cell in enumerate(row_data)
        ])
        excel_rows += f'<tr class="{bg_class}">{cells}</tr>\n'
    
    # Generate column specification rows
    column_rows = ''.join([
        f'''<tr class="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">{col["name"]}</td>
                <td class="px-4 py-3"><span class="px-2 py-1 text-xs font-medium {"bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300" if col["required"] else "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300"} rounded">{"Required" if col["required"] else "Optional"}</span></td>
                <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{col["description"]}{" (e.g., " + col["example"] + ")" if col["example"] and not col["example"].startswith("Leave") else ""}</td>
            </tr>'''
        for col in config['columns']
    ])
    
    # Generate Pro Tips list
    pro_tips = ''.join([f'<li>{tip}</li>\n' for tip in config['pro_tips']])
    
    # Generate Important Notes list
    important_notes = ''.join([
        f'<li class="flex items-start"><i class="fas fa-arrow-right text-amber-600 dark:text-amber-400 mt-1 mr-2 text-xs"></i><span>{note}</span></li>\n'
        for note in config['important_notes']
    ])
    
    modal_html = f'''<!-- Import {config["title"]} Modal -->
<div id="import-{entity}-modal" class="fixed inset-0 bg-gray-900/80 backdrop-blur-sm hidden items-center justify-center z-[9999] p-4 transition-all duration-300">
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[95vh] overflow-hidden transform transition-all duration-300 scale-95 opacity-0 modal-content">
        <!-- Modal Header -->
        <div class="bg-gradient-to-r from-primary to-tertiary px-8 py-6 flex items-center justify-between sticky top-0 z-10">
            <div class="flex items-center space-x-3">
                <div class="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                    <i class="fas fa-file-import text-white text-2xl"></i>
                </div>
                <div>
                    <h3 class="text-2xl font-bold text-white">Import {config["title"]}</h3>
                    <p class="text-blue-100 text-sm mt-1">{config["subtitle"]}</p>
                </div>
            </div>
            <button type="button" id="close-import-{entity}-modal" class="text-white/80 hover:text-white hover:bg-white/20 rounded-lg p-2 transition-all duration-200">
                <i class="fas fa-times text-xl"></i>
            </button>
        </div>

        <!-- Modal Body -->
        <div class="p-8 overflow-y-auto max-h-[calc(95vh-180px)] custom-scrollbar">
            <!-- Instructions -->
            <div class="mb-8 p-6 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded-lg">
                <h4 class="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3 flex items-center">
                    <i class="fas fa-info-circle mr-2"></i> File Format Instructions
                </h4>
                <div class="space-y-3 text-sm text-blue-800 dark:text-blue-200">
                    <p class="flex items-start">
                        <i class="fas fa-check-circle text-blue-600 dark:text-blue-400 mt-0.5 mr-2"></i>
                        <span><strong>Download Template:</strong> Click "Download Template" button to get the correct Excel format with all required columns</span>
                    </p>
                    <p class="flex items-start">
                        <i class="fas fa-check-circle text-blue-600 dark:text-blue-400 mt-0.5 mr-2"></i>
                        <span><strong>Supported Formats:</strong> Excel files (.xlsx, .xls) and CSV files (.csv)</span>
                    </p>
                    <p class="flex items-start">
                        <i class="fas fa-check-circle text-blue-600 dark:text-blue-400 mt-0.5 mr-2"></i>
                        <span><strong>Maximum Size:</strong> 10MB per file</span>
                    </p>
                </div>
            </div>

            <!-- Template Download Section -->
            <div class="mb-8 p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl border border-green-200 dark:border-green-800">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="p-3 bg-green-100 dark:bg-green-800 rounded-lg">
                            <i class="fas fa-file-excel text-green-600 dark:text-green-300 text-3xl"></i>
                        </div>
                        <div>
                            <h5 class="text-lg font-semibold text-gray-900 dark:text-white">{config["title"]} Import Template</h5>
                            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">Excel template with proper format and column headers</p>
                        </div>
                    </div>
                    <a href="{{% url '{config["template_url"]}' %}}" 
                       class="inline-flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5">
                        <i class="fas fa-download mr-2"></i>
                        Download Template
                    </a>
                </div>
            </div>

            <!-- Column Specifications Table -->
            <div class="mb-8">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                    <i class="fas fa-table text-primary mr-2"></i>
                    Required Columns and Format
                </h4>
                <div class="overflow-hidden border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
                    <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead class="bg-gray-50 dark:bg-gray-900">
                            <tr>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Column</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Required</th>
                                <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Format/Description</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700 text-sm">
                            {column_rows}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Excel Format Preview -->
            <div class="mb-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h5 class="font-medium text-blue-900 dark:text-blue-100 mb-3 flex items-center">
                    <i class="fas fa-file-excel text-green-600 mr-2"></i>
                    Excel/CSV Format Preview (Matches Export Format):
                </h5>
                
                <!-- Excel-style table preview -->
                <div class="bg-white dark:bg-gray-800 rounded border overflow-x-auto">
                    <table class="w-full text-xs border-collapse">
                        <thead>
                            <tr style="background-color: #1F4E78;">
                                {excel_headers}
                            </tr>
                        </thead>
                        <tbody class="text-gray-800 dark:text-gray-200">
                            {excel_rows}
                        </tbody>
                    </table>
                </div>
                
                <div class="mt-3 flex items-start space-x-2">
                    <div class="flex-shrink-0 mt-1">
                        <i class="fas fa-info-circle text-blue-600 dark:text-blue-400"></i>
                    </div>
                    <div class="text-xs text-blue-700 dark:text-blue-300">
                        <p class="font-semibold mb-1">Pro Tips:</p>
                        <ul class="list-disc list-inside space-y-0.5">
                            {pro_tips}
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Important Notes -->
            <div class="mb-8 p-6 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500 rounded-lg">
                <h4 class="text-lg font-semibold text-amber-900 dark:text-amber-100 mb-3 flex items-center">
                    <i class="fas fa-exclamation-triangle mr-2"></i> Important Notes
                </h4>
                <ul class="space-y-2 text-sm text-amber-800 dark:text-amber-200">
                    {important_notes}
                </ul>
            </div>

            <!-- File Upload Section -->
            <div class="mb-6">
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                    <i class="fas fa-cloud-upload-alt text-primary mr-2"></i>
                    Upload File
                </h4>
                <form id="import-{entity}-form" class="space-y-4">
                    {{% csrf_token %}}
                    <div class="flex items-center justify-center w-full">
                        <label for="import-{entity}-file" class="flex flex-col items-center justify-center w-full h-48 border-2 border-gray-300 dark:border-gray-600 border-dashed rounded-xl cursor-pointer bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 group">
                            <div class="flex flex-col items-center justify-center pt-5 pb-6">
                                <i class="fas fa-cloud-upload-alt text-5xl text-gray-400 dark:text-gray-500 group-hover:text-primary dark:group-hover:text-tertiary mb-3 transition-colors"></i>
                                <p class="mb-2 text-sm text-gray-500 dark:text-gray-400">
                                    <span class="font-semibold">Click to upload</span> or drag and drop
                                </p>
                                <p class="text-xs text-gray-500 dark:text-gray-400">Excel (.xlsx, .xls) or CSV files (MAX. 10MB)</p>
                                <p id="import-{entity}-file-name" class="mt-2 text-sm font-medium text-primary dark:text-tertiary hidden"></p>
                            </div>
                            <input id="import-{entity}-file" name="file" type="file" class="hidden" accept=".xlsx,.xls,.csv" />
                        </label>
                    </div>

                    <!-- Progress Bar -->
                    <div id="import-{entity}-progress" class="hidden">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Importing {entity}...</span>
                            <span class="text-sm font-medium text-gray-700 dark:text-gray-300" id="import-{entity}-progress-percent">0%</span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                            <div id="import-{entity}-progress-bar" class="bg-gradient-to-r from-primary to-tertiary h-3 rounded-full transition-all duration-300 ease-out" style="width: 0%"></div>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- Modal Footer -->
        <div class="bg-gray-50 dark:bg-gray-900 px-8 py-6 flex items-center justify-end space-x-3 border-t border-gray-200 dark:border-gray-700 sticky bottom-0">
            <button type="button" id="cancel-import-{entity}" class="px-6 py-2.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200 shadow-sm">
                <i class="fas fa-times mr-2"></i> Cancel
            </button>
            <button type="button" id="submit-import-{entity}" class="px-6 py-2.5 bg-gradient-to-r from-primary to-tertiary text-white font-medium rounded-lg hover:shadow-lg transition-all duration-200 transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none">
                <i class="fas fa-upload mr-2"></i> Import {config["title"]}
            </button>
        </div>
    </div>
</div>'''
    
    return modal_html

# Generate all modals
if __name__ == '__main__':
    for entity_key in MODAL_CONFIGS.keys():
        html = generate_modal_html(entity_key)
        output_file = f'modal_{entity_key}.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Generated {output_file}")
    
    print("\nAll modal HTML files generated successfully!")
    print("\nNext steps:")
    print("1. Review each generated modal file")
    print("2. Replace the old modals in the respective template files")
    print("3. Update any JavaScript handlers to match new element IDs")
