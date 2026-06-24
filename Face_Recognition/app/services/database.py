"""
Database Utilities
Helper functions for database operations, backup, and maintenance
"""

import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from app.models.models import db
from flask import current_app
import logging

logger = logging.getLogger(__name__)


def backup_database(backup_dir='data/backups', prefix='attendance'):
    """
    Create backup of database file
    Returns backup path if successful, None otherwise
    """
    try:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        db_file = Path('data/attendance.db')
        if not db_file.exists():
            logger.warning('Database file not found, skipping backup')
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_path / f'{prefix}_backup_{timestamp}.db'
        
        shutil.copy2(db_file, backup_file)
        
        backup_size = backup_file.stat().st_size
        logger.info(f'Database backup created: {backup_file} ({backup_size / 1024 / 1024:.2f} MB)')
        
        return str(backup_file)
    except Exception as e:
        logger.error(f'Failed to create database backup: {e}')
        return None


def cleanup_old_backups(backup_dir='data/backups', keep_last=10, prefix='attendance'):
    """
    Clean up old backups, keeping only the most recent ones
    """
    try:
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            return
        
        # Get all backup files matching prefix
        backup_files = sorted(
            backup_path.glob(f'{prefix}_backup_*.db'),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        # Remove old backups
        removed = []
        for old_backup in backup_files[keep_last:]:
            old_backup.unlink()
            removed.append(str(old_backup))
        
        if removed:
            logger.info(f'Cleaned up {len(removed)} old backups: {removed}')
        
        return removed
    except Exception as e:
        logger.error(f'Failed to cleanup old backups: {e}')
        return []


def auto_backup_database():
    """
    Automatic backup with cleanup
    Call this periodically or on important operations
    """
    backup_dir = 'data/backups'
    max_backups = int(os.environ.get('MAX_BACKUPS', '10'))
    
    # Create backup
    backup_path = backup_database(backup_dir=backup_dir)
    
    if backup_path:
        # Cleanup old backups
        cleanup_old_backups(backup_dir=backup_dir, keep_last=max_backups)
        return True
    
    return False


def backup_json_csv_data(backup_dir='data/backups'):
    """Backup original JSON/CSV files before migration"""
    try:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        files_to_backup = [
            'data/students.json',
            'data/encodings.pkl',
            'data/attendance.csv'
        ]

        backed_up = []

        for file_path in files_to_backup:
            source = Path(file_path)
            if source.exists():
                dest = backup_path / f'{source.stem}_backup_{timestamp}{source.suffix}'
                shutil.copy2(source, dest)
                backed_up.append(str(dest))
        
        if backed_up:
            logger.info(f'Backed up {len(backed_up)} data files')

        return backed_up
    except Exception as e:
        logger.error(f'Failed to backup data files: {e}')
        return []


def get_db_connection():
    """Get database connection (for raw SQL if needed)"""
    return db.engine.connect()


def execute_query(query, params=None):
    """Execute raw SQL query"""
    with get_db_connection() as conn:
        result = conn.execute(query, params or {})
        return result


def get_database_stats():
    """Get database statistics"""
    from app.models.models import Student, Attendance, User

    stats = {
        'total_students': Student.query.filter_by(is_active=True).count(),
        'total_attendance_records': Attendance.query.count(),
        'total_users': User.query.filter_by(is_active=True).count(),
        'database_size': get_database_size(),
        'total_backups': get_backup_count(),
        'latest_backup': get_latest_backup(),
    }

    return stats


def get_database_size():
    """Get database file size in bytes"""
    db_file = Path('data/attendance.db')
    if db_file.exists():
        return db_file.stat().st_size
    return 0


def get_backup_count(backup_dir='data/backups'):
    """Get number of backups"""
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        return 0
    return len(list(backup_path.glob('attendance_backup_*.db')))


def get_latest_backup(backup_dir='data/backups'):
    """Get latest backup timestamp"""
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        return None
    
    backup_files = sorted(
        backup_path.glob('attendance_backup_*.db'),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    
    if not backup_files:
        return None
    
    latest = backup_files[0]
    return {
        'path': str(latest),
        'timestamp': datetime.fromtimestamp(latest.stat().st_mtime),
        'size': latest.stat().st_size
    }


def optimize_database():
    """Optimize database (vacuum, analyze)"""
    try:
        db.session.execute('VACUUM')
        db.session.execute('ANALYZE')
        db.session.commit()
        logger.info('Database optimized')
    except Exception as e:
        logger.error(f'Failed to optimize database: {e}')


def check_database_health():
    """Check database health and integrity"""
    try:
        # Try a simple query
        db.session.execute('SELECT 1')
        
        # Check file exists
        db_file = Path('data/attendance.db')
        if not db_file.exists():
            return {'healthy': False, 'message': 'Database file not found'}
        
        # Check file size
        size = db_file.stat().st_size
        if size == 0:
            return {'healthy': False, 'message': 'Database file is empty'}
        
        return {
            'healthy': True,
            'message': 'Database is healthy',
            'size': size,
            'path': str(db_file)
        }
    except Exception as e:
        return {'healthy': False, 'message': f'Database error: {str(e)}'}


def init_database_directories():
    """Initialize required directories"""
    directories = [
        'data',
        'data/students',
        'data/backups',
        'static/uploads'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
