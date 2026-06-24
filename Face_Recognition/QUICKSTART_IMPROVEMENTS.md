# 🚀 Quick Start Guide - After Improvements

## Setup Instructions

### 1. Generate Secret Key (REQUIRED)
```bash
# Windows Command Prompt
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"

# Copy the output and add to .env file
```

### 2. Create/Update .env File

**Windows (Command Prompt):**
```cmd
copy .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux/Mac:**
```bash
cp .env.example .env
```

**Then edit .env and set at minimum:**
```env
SECRET_KEY=<paste-your-generated-key-here>
```

### 3. Change Default Admin Password
1. Login with `admin` / `admin1234`
2. Navigate to `/change_password`
3. Use a strong password (min 8 chars, uppercase, lowercase, number)

### 4. Run the Application

**Windows (Command Prompt):**
```cmd
python run.py
```

**Windows (PowerShell):**
```powershell
python run.py
```

**Linux/Mac:**
```bash
python3 run.py
# atau
python run.py
```

**Access the app at:** `http://localhost:5000`

---

## New Features Quick Reference

### 🔐 Password Change
- **URL:** `/change_password`
- **Requirements:** 8+ chars, uppercase, lowercase, number
- **API:** `POST /api/validate_password` for real-time validation

### 💾 Database Backup
- **Manual Backup:** `POST /backup_database` (admin only)
- **View Stats:** `GET /api/database_stats` (admin only)
- **Cleanup:** `POST /api/cleanup_backups` with `keep_count` parameter

### 👨‍🎓 Student Management
- **Soft Delete:** Default - marks as inactive, keeps photos
- **Hard Delete:** Send `delete_photos=true` in form - removes everything
- **NISN Support:** Now accepts 6-10 digit IDs (configurable)

### 📊 Monitoring
- **Health Check:** `GET /health`
- **Readiness:** `GET /ready`
- **Cache Stats:** `FaceCache.get_cache_stats()` in Python
- **DB Stats:** `GET /api/database_stats`

---

## Configuration Options

### NISN Validation
```env
MIN_NISN_LENGTH=6   # Minimum digits (default: 6)
MAX_NISN_LENGTH=10  # Maximum digits (default: 10)
```

### Face Cache
```python
# In your code (default TTL: 300 seconds / 5 minutes)
from app.services.face_service import FaceCache
FaceCache.set_ttl(600)  # Set to 10 minutes
```

### Database Backups
```env
MAX_BACKUPS=10  # Number of backups to keep (default: 10)
```

### Logging
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=data/app.log
```

---

## What Changed?

### Security
✅ Auto-generated secret key instead of hardcoded default  
✅ Attendance race condition prevented with unique constraint  
✅ Password strength validation on change  
✅ NISN validation more flexible (6-10 digits)  

### Performance
✅ Face cache auto-expires after 5 minutes  
✅ Camera resources properly cleaned up  
✅ Structured logging for better monitoring  

### Reliability  
✅ Automated database backup on startup  
✅ Old backups automatically cleaned up  
✅ Student photos can be hard deleted  
✅ Better error handling throughout  

---

## Troubleshooting

### App Won't Start
1. Check if SECRET_KEY is set in `.env`
2. Review `data/app.log` for errors
3. Run with `FLASK_DEBUG=1` for verbose output

### Camera Not Working
1. Check `CAMERA_INDEX` in `.env`
2. Review logs for camera initialization errors
3. Ensure no other app is using the camera

### Database Backup Failed
1. Check `data/backups/` directory permissions
2. Review logs for specific error messages
3. Ensure database file exists

### Password Change Not Working
1. Verify current password is correct
2. Check new password meets all requirements
3. Review browser console for JavaScript errors

---

## File Structure Changes

### New Files
```
app/
├── utils/
│   ├── __init__.py          # NEW
│   └── password.py          # NEW - Password validation
└── templates/
    └── change_password.html # NEW - Password change UI
```

### Modified Files
See `IMPROVEMENTS.md` for complete list of changes.

---

**Need Help?** Check `IMPROVEMENTS.md` for detailed documentation.
