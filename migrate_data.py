"""
Data Migration Script
Migrate data from JSON/CSV files to SQLite database
"""

import json
import pickle
from pathlib import Path
from datetime import datetime
import pandas as pd
from app import create_app
from app.models.models import db, Student, Attendance
from app.services.database import backup_json_csv_data, init_database_directories

def migrate_data():
    """Main migration function"""
    print("=" * 70)
    print(" DATA MIGRATION: JSON/CSV → SQLite Database")
    print("=" * 70)
    
    # Initialize Flask app for database context
    app = create_app()
    
    with app.app_context():
        # Step 1: Backup existing data
        print("\n[1/4] Backing up existing data...")
        backed_up_files = backup_json_csv_data()
        if backed_up_files:
            print(f"✓ Backed up {len(backed_up_files)} files:")
            for file in backed_up_files:
                print(f"  - {file}")
        else:
            print("⚠ No existing data files found to backup")
        
        # Step 2: Migrate students
        print("\n[2/4] Migrating student data...")
        students_migrated = migrate_students()
        print(f"✓ Migrated {students_migrated} students")
        
        # Step 3: Migrate attendance
        print("\n[3/4] Migrating attendance records...")
        attendance_migrated = migrate_attendance()
        print(f"✓ Migrated {attendance_migrated} attendance records")
        
        # Step 4: Verify migration
        print("\n[4/4] Verifying migration...")
        verify_migration(students_migrated, attendance_migrated)
        
        print("\n" + "=" * 70)
        print(" MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\n✓ Database: data/attendance.db")
        print(f"✓ Students: {students_migrated}")
        print(f"✓ Attendance: {attendance_migrated}")
        print(f"✓ Backups: data/backups/")
        print("\n⚠ Old files are preserved in data/backups/")
        print("  You can safely delete them after verifying the migration.")
        print("=" * 70)


def migrate_students():
    """Migrate students from JSON and encodings from pickle"""
    students_file = Path('data/students.json')
    encodings_file = Path('data/encodings.pkl')
    
    if not students_file.exists():
        print("  ⚠ No students.json found")
        return 0
    
    # Load students data
    with open(students_file, 'r') as f:
        students_data = json.load(f)
    
    # Load encodings
    encodings_map = {}
    if encodings_file.exists():
        with open(encodings_file, 'rb') as f:
            encodings_data = pickle.load(f)
            known_encodings = encodings_data.get('encodings', [])
            known_names = encodings_data.get('names', [])
            
            # Map student_id to their encodings
            for encoding, student_id in zip(known_encodings, known_names):
                if student_id not in encodings_map:
                    encodings_map[student_id] = []
                encodings_map[student_id].append(encoding)
    
    count = 0
    for student_id, data in students_data.items():
        # Check if already exists
        existing = Student.query.filter_by(student_id=student_id).first()
        if existing:
            print(f"  ⚠ Student {student_id} already exists, skipping")
            continue
        
        # Create new student
        student = Student(
            student_id=student_id,
            name=data.get('name', ''),
            class_name=data.get('class', ''),
            num_photos=data.get('num_photos', 0),
            added_date=datetime.strptime(data.get('added_date', str(datetime.now().date())), '%Y-%m-%d').date()
        )
        
        # Set photos
        photos = data.get('photos', [])
        student.set_photos(photos)
        
        # Set encodings
        if student_id in encodings_map:
            student.set_face_encodings(encodings_map[student_id])
        
        db.session.add(student)
        count += 1
        print(f"  + {student_id}: {data.get('name')}")
    
    db.session.commit()
    return count


def migrate_attendance():
    """Migrate attendance from CSV"""
    attendance_file = Path('data/attendance.csv')
    
    if not attendance_file.exists():
        print("  ⚠ No attendance.csv found")
        return 0
    
    # Read CSV
    df = pd.read_csv(attendance_file)
    
    if len(df) == 0:
        return 0
    
    count = 0
    for _, row in df.iterrows():
        student_id = str(row.get('StudentID', ''))
        date_str = str(row.get('Date', ''))
        time_str = str(row.get('Time', ''))
        
        # Parse date and time
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            print(f"  ⚠ Invalid date: {date_str}, skipping")
            continue
        
        try:
            time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
        except Exception:
            try:
                time_obj = datetime.strptime(time_str, '%H:%M').time()
            except Exception:
                print(f"  ⚠ Invalid time: {time_str}, skipping")
                continue
        
        # Check if already exists
        existing = Attendance.query.filter_by(
            student_id=student_id,
            date=date_obj,
            time=time_obj
        ).first()
        
        if existing:
            continue
        
        # Verify student exists
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            print(f"  ⚠ Student {student_id} not found, skipping attendance record")
            continue
        
        # Create attendance record
        attendance = Attendance(
            student_id=student_id,
            date=date_obj,
            time=time_obj,
            status=row.get('Status', 'Present'),
            marked_by='auto'
        )
        
        db.session.add(attendance)
        count += 1
        
        if count % 100 == 0:
            print(f"  + Migrated {count} records...")
    
    db.session.commit()
    return count


def verify_migration(expected_students, expected_attendance):
    """Verify migration was successful"""
    actual_students = Student.query.count()
    actual_attendance = Attendance.query.count()
    
    if actual_students != expected_students:
        print(f"  ⚠ WARNING: Expected {expected_students} students, got {actual_students}")
    else:
        print(f"  ✓ Students verified: {actual_students}")
    
    if actual_attendance != expected_attendance:
        print(f"  ⚠ WARNING: Expected {expected_attendance} attendance records, got {actual_attendance}")
    else:
        print(f"  ✓ Attendance verified: {actual_attendance}")
    
    # Test query
    try:
        latest = Attendance.query.order_by(Attendance.created_at.desc()).first()
        if latest:
            print(f"  ✓ Latest attendance: {latest.student_id} on {latest.date}")
    except Exception as e:
        print(f"  ⚠ Error querying database: {e}")


if __name__ == '__main__':
    migrate_data()
