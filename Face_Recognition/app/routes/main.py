from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app, send_file
from datetime import date, timedelta
from app.models.models import Student, Attendance, db, get_setting, set_setting
from app.services.camera_service import CAMERA_ENABLED, RECOGNITION_ENABLED
from app.services.database import backup_database, get_database_stats, check_database_health, cleanup_old_backups
from functools import wraps
from pathlib import Path

main_bp = Blueprint('main', __name__)

def admin_required(view_func):
    """Decorator for admin-only routes"""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('is_admin'):
            next_url = request.path
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('auth.login', next=next_url))
        return view_func(*args, **kwargs)
    return wrapped

@main_bp.route('/')
def index():
    """Home page with advanced analytics"""
    total_students = Student.query.filter_by(is_active=True).count()
    today = date.today()
    
    # Basic stats
    today_attendance = Attendance.query.filter_by(date=today).count()
    total_records = Attendance.query.count()
    
    # Session stats
    morning_present = Attendance.query.filter_by(date=today, session_type='morning').count()
    afternoon_present = Attendance.query.filter_by(date=today, session_type='afternoon').count()
    
    # Late stats
    late_today = Attendance.query.filter_by(date=today, status='Late').count()
    on_time_today = today_attendance - late_today
    
    today_percentage = round(
        (today_attendance / total_students * 100) if total_students > 0 else 0, 
        1
    )
    
    stats = {
        'total_students': total_students,
        'today_present': today_attendance,
        'total_records': total_records,
        'today_percentage': today_percentage,
        'morning_present': morning_present,
        'afternoon_present': afternoon_present,
        'late_today': late_today,
        'on_time_today': on_time_today
    }
    
    # Calculate last 7 days attendance
    dates = []
    counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.session.query(Attendance.student_id).filter_by(date=day).distinct().count()
        dates.append(day.strftime('%d %b'))
        counts.append(count)
    
    # Class-wise attendance (Today)
    class_stats = db.session.query(Student.class_name, db.func.count(Attendance.id))\
        .join(Attendance, Student.student_id == Attendance.student_id)\
        .filter(Attendance.date == today)\
        .group_by(Student.class_name).all()
    
    class_labels = [row[0] for row in class_stats]
    class_data = [row[1] for row in class_stats]
    
    chart_data = {
        'labels': dates,
        'data': counts,
        'class_labels': class_labels,
        'class_data': class_data
    }
    
    return render_template('index.html', stats=stats, chart_data=chart_data)


@main_bp.route('/health')
def health():
    """Simple health check for runtime monitoring."""
    db_ok = True
    db_error = None

    try:
        db.session.execute(db.select(1)).scalar()
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    status = 'ok' if db_ok else 'degraded'
    payload = {
        'status': status,
        'database': 'ok' if db_ok else 'error',
        'camera_enabled': bool(CAMERA_ENABLED),
        'recognition_enabled': bool(RECOGNITION_ENABLED),
    }
    if db_error:
        payload['database_error'] = db_error

    return jsonify(payload), (200 if db_ok else 503)


@main_bp.route('/ready')
def ready():
    """Readiness probe for orchestration and uptime checks."""
    try:
        db.session.execute(db.select(1)).scalar()
        return jsonify({'ready': True, 'database': 'ok'}), 200
    except Exception as exc:
        return jsonify({'ready': False, 'database': 'error', 'error': str(exc)}), 503

@main_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """System settings management"""
    if request.method == 'POST':
        keys = [
            'morning_session_start', 'morning_session_end',
            'afternoon_session_start', 'afternoon_session_end',
            'late_threshold_minutes', 'attendance_enabled'
        ]
        for key in keys:
            if key in request.form:
                value = request.form[key]
                if key == 'attendance_enabled':
                    value = 'true' if value == 'on' else 'false'
                set_setting(key, value)
        
        flash('Pengaturan berhasil diperbarui.', 'success')
        return redirect(url_for('main.settings'))

    all_settings = {
        'late_threshold_minutes': get_setting('late_threshold_minutes', '15'),
        'morning_session_start': get_setting('morning_session_start', '07:00'),
        'morning_session_end': get_setting('morning_session_end', '12:00'),
        'afternoon_session_start': get_setting('afternoon_session_start', '13:00'),
        'afternoon_session_end': get_setting('afternoon_session_end', '17:00'),
        'attendance_enabled': get_setting('attendance_enabled', 'true'),
    }
    
    return render_template('settings.html', settings=all_settings)


@main_bp.route('/backup_database', methods=['POST'])
@admin_required
def backup_database_route():
    """Create database backup (admin only)"""
    try:
        backup_path = backup_database()
        if backup_path:
            flash(f'Backup berhasil dibuat: {Path(backup_path).name}', 'success')
            current_app.logger.info(f'Manual database backup created: {backup_path}')
        else:
            flash('Gagal membuat backup', 'error')
    except Exception as e:
        current_app.logger.error(f'Backup failed: {e}')
        flash(f'Terjadi kesalahan saat backup: {e}', 'error')
    
    return redirect(url_for('main.settings'))


@main_bp.route('/api/database_stats')
@admin_required
def api_database_stats():
    """API endpoint for database statistics"""
    try:
        stats = get_database_stats()
        health = check_database_health()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'health': health
        })
    except Exception as e:
        current_app.logger.error(f'Failed to get database stats: {e}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@main_bp.route('/api/cleanup_backups', methods=['POST'])
@admin_required
def api_cleanup_backups():
    """API endpoint to cleanup old backups"""
    try:
        keep_count = int(request.form.get('keep_count', 10))
        removed = cleanup_old_backups(keep_last=keep_count)
        
        flash(f'Berhasil menghapus {len(removed)} backup lama', 'success')
        current_app.logger.info(f'Backup cleanup: removed {len(removed)} old backups')
        
        return jsonify({
            'success': True,
            'removed_count': len(removed),
            'removed_files': removed
        })
    except Exception as e:
        current_app.logger.error(f'Backup cleanup failed: {e}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
