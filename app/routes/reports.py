from flask import Blueprint, render_template, send_file, request, current_app
from app.models.models import Attendance, Student, db
from app.routes.main import admin_required
from datetime import datetime, date, timedelta
import io
import openpyxl

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@admin_required
def reports():
    """Reports page"""
    today = date.today()
    default_start = today.replace(day=1)
    
    start_date = request.args.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', today.strftime('%Y-%m-%d'))
    class_filter = request.args.get('class_filter', '')
    
    query = Attendance.query.filter(Attendance.date >= start_date, Attendance.date <= end_date)
    
    if class_filter:
        query = query.join(Student).filter(Student.class_name == class_filter)
        
    records = query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()
    
    classes = db.session.query(Student.class_name).distinct().all()
    classes = [c[0] for c in classes]
    
    return render_template('reports.html', 
                          records=records,
                          classes=classes,
                          start_date=start_date,
                          end_date=end_date,
                          class_filter=class_filter)

@reports_bp.route('/export_excel')
@admin_required
def export_excel():
    """Export reports to Excel"""
    today = date.today()
    default_start = today.replace(day=1)
    
    start_date = request.args.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', today.strftime('%Y-%m-%d'))
    class_filter = request.args.get('class_filter', '')
    
    query = Attendance.query.filter(Attendance.date >= start_date, Attendance.date <= end_date)
    
    if class_filter:
        query = query.join(Student).filter(Student.class_name == class_filter)
        
    records = query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Laporan Absensi"
    
    headers = ['Tanggal', 'Jam', 'ID Siswa', 'Nama', 'Kelas', 'Status', 'Sesi', 'Confidence', 'Notes']
    ws.append(headers)
    
    for record in records:
        ws.append([
            record.date,
            record.time,
            record.student.student_id if record.student else record.student_id,
            record.student.name if record.student else 'Unknown',
            record.student.class_name if record.student else '',
            record.status,
            record.session_type,
            f"{int(record.confidence * 100)}%" if record.confidence else '',
            record.notes or ''
        ])
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"laporan_absensi_{start_date}_{end_date}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
