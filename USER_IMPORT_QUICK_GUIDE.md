# User Import/Export - Quick Reference Guide

## 🚀 Quick Start

### Export Users
1. Go to **Admin → Users**
2. Click the green **"Export"** button
3. Choose format: **Excel**, **PDF**, or **Word**
4. File downloads automatically with timestamp

### Import Users
1. Go to **Admin → Users**
2. Click the blue **"Import"** button
3. Select your CSV or Excel file
4. Click **"Import Users"**
5. Review results

---

## 📋 File Format

### The Easy Way
**Export existing users and use that file as your template!**
- Export includes all the right columns
- Just modify the data you need
- Re-import to update or add users

### Column Reference

| Column | Required? | Example |
|--------|-----------|---------|
| Username | ✅ Yes | john.doe |
| Email | ✅ Yes | john.doe@school.edu |
| First Name | ✅ Yes | John |
| Last Name | ✅ Yes | Doe |
| Role | ✅ Yes | Teacher |
| Password | ✅ Yes | Password123 |
| Middle Name | ❌ No | Smith |
| Status | ❌ No | Active |
| ID | ❌ No | (ignored) |
| Created Date | ❌ No | (ignored) |

---

## 💡 Import Behaviors

### New Users
If username doesn't exist → **Creates new user**

### Existing Users
If username exists → **Updates all information**

### Duplicates
- Same username → Updates existing
- Same email (different user) → Skipped with error

---

## 🎯 Common Use Cases

### 1. Bulk Create Teachers
```csv
Username,Email,First Name,Last Name,Role,Password
teacher1,teacher1@school.edu,John,Smith,Teacher,Pass123456
teacher2,teacher2@school.edu,Jane,Doe,Teacher,Pass123456
teacher3,teacher3@school.edu,Bob,Johnson,Teacher,Pass123456
```

### 2. Update User Roles
1. Export users
2. Change "Role" column for specific users
3. Re-import → Roles updated!

### 3. Bulk Password Reset
1. Export users
2. Change "Password" column
3. Re-import → Passwords updated!

### 4. Activate/Deactivate Users
1. Export users
2. Change "Status" to "Active" or "Inactive"
3. Re-import → Status updated!

---

## ✅ Valid Values

### Roles
- `Teacher` or `TEACHER`
- `Principal` or `PRINCIPAL`
- `Registrar` or `REGISTRAR`
- `Admin` or `ADMIN` or `Administrator`

### Status
- `Active` or `Inactive`
- `TRUE` or `FALSE`
- `1` or `0`
- Leave blank = Active

---

## 🛡️ Validation Rules

### Username
- Must be unique
- Cannot be empty

### Email
- Must be unique
- Must be valid email format
- Cannot be empty

### Password
- Minimum 8 characters
- Cannot be empty

### Role
- Must be one of: Admin, Teacher, Principal, Registrar
- Case-insensitive

---

## ⚠️ Common Errors & Solutions

### "Missing required columns"
**Solution**: Make sure your file has headers:
`Username,Email,First Name,Last Name,Role,Password`

### "Username already exists"
**This is OK!** → It will update the existing user
If you don't want to update, remove that row.

### "Email already exists"
**Solution**: Each email can only be used once
Check if email is used by a different username.

### "Password must be at least 8 characters"
**Solution**: Use passwords with 8+ characters
Example: `Password123` or `TempPass2024`

### "Invalid role"
**Solution**: Use one of these: Teacher, Principal, Registrar, Admin

---

## 📊 File Formats

### CSV Example
```csv
Username,Email,First Name,Last Name,Middle Name,Role,Status,Password
john.doe,john@school.edu,John,Doe,Smith,Teacher,Active,Pass123456
jane.doe,jane@school.edu,Jane,Doe,,Admin,Active,AdminPass123
```

### Excel Example
Same columns, but in Excel format (.xlsx or .xls)
- Easier to edit
- Better for large datasets
- Can use formulas

---

## 🎨 Pro Tips

1. **Use Export as Template**
   - Export current users
   - Save as "template.xlsx"
   - Use for future imports

2. **Test with Small File First**
   - Import 2-3 users first
   - Verify format works
   - Then import the rest

3. **Keep Backups**
   - Export before large imports
   - You can always re-import to restore

4. **Use Excel for Editing**
   - Easier than CSV
   - Better error prevention
   - Can sort/filter data

5. **Check Results**
   - Always review the import summary
   - Check for skipped rows
   - Fix errors and re-import

---

## 📁 File Requirements

- **Maximum Size**: 10MB
- **Supported Formats**: .csv, .xlsx, .xls
- **Character Encoding**: UTF-8 (default in Excel)

---

## 🔄 Workflow Example

1. **Export Current Users**
   ```
   Click Export → Choose Excel → Save file
   ```

2. **Add New Users**
   ```
   Open exported file → Add rows → Save
   ```

3. **Import Updated File**
   ```
   Click Import → Select file → Import Users
   ```

4. **Review Results**
   ```
   Check: X created, Y updated, Z skipped
   ```

5. **Fix Any Errors**
   ```
   Read error messages → Fix data → Re-import
   ```

---

## 🆘 Need Help?

### Download Template
Click "Download Template" in the import modal to get a sample file.

### Check Export Format
Export some users to see the exact format expected.

### Read Error Messages
Error messages include row numbers and specific issues.

---

## ⚡ Quick Checklist

Before importing, make sure:
- [ ] File has required columns
- [ ] Usernames are unique in your file
- [ ] Emails are unique in your file
- [ ] Passwords are 8+ characters
- [ ] Roles are valid (Teacher, Principal, etc.)
- [ ] File is under 10MB
- [ ] File format is CSV, XLSX, or XLS

---

**Happy Importing! 🎉**
