from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file, send_from_directory, abort
from werkzeug.utils import secure_filename
from app.models.models import Student, db
from app.services.face_service import FaceCache
from app.routes.main import admin_required
from pathlib import Path
from datetime import date, datetime
import re
try:
    import face_recognition
except ImportError:
    face_recognition = None
from PIL import Image
import io
import csv
import shutil

students_bp = Blueprint('students', __name__)

RECOGNITION_ENABLED = face_recognition is not None


def is_valid_nisn(student_id):
    """
    NISN validation: Support 6-10 digits for flexibility
    - Old data may have 6 digits
    - New NISN standard is 10 digits
    - Configurable via MIN_NISN_LENGTH and MAX_NISN_LENGTH
    """
    import re
    min_length = current_app.config.get('MIN_NISN_LENGTH', 6)
    max_length = current_app.config.get('MAX_NISN_LENGTH', 10)
    pattern = r'^\d{' + str(min_length) + r',' + str(max_length) + r'}$'
    return bool(re.fullmatch(pattern, student_id))

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def client_wants_json():
    """Check if client prefers JSON response"""
    best = request.accept_mimetypes.best
    return best == 'application/json' and \
           request.accept_mimetypes[best] > request.accept_mimetypes['text/html']

@students_bp.route('/students')
@admin_required
def students():
    """Students management page"""
    students_list = Student.query.filter_by(is_active=True).order_by(Student.name).all()
    
    # Convert to dict format for template compatibility
    students_dict = {}
    for student in students_list:
        students_dict[student.student_id] = {
            'id': student.id,
            'name': student.name,
            'class': student.class_name,
            'gender': student.gender,
            'birth_place': student.birth_place,
            'birth_date': str(student.birth_date) if student.birth_date else '-',
            'religion': student.religion,
            'address': student.address,
            'num_photos': student.num_photos,
            'added_date': str(student.added_date),
            'photos': student.get_photos()
        }
    
    return render_template('students.html', students=students_dict)

@students_bp.route('/add_student', methods=['GET', 'POST'])
@admin_required
def add_student():
    """Add new student"""
    if request.method == 'POST':
        wants_json = client_wants_json()

        student_id = (request.form.get('student_id') or '').strip()
        name = (request.form.get('name') or '').strip()
        class_name = (request.form.get('class_name') or '').strip()
        gender = (request.form.get('gender') or '').strip()
        birth_place = (request.form.get('birth_place') or '').strip()
        birth_date_raw = (request.form.get('birth_date') or '').strip()
        religion = (request.form.get('religion') or '').strip()
        address = (request.form.get('address') or '').strip()

        # Validation
        if not is_valid_nisn(student_id):
            message = 'NISN/Identification ID harus 10 digit angka.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        if Student.query.filter_by(student_id=student_id).first():
            message = 'Student ID sudah terdaftar.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        if not name or not class_name:
            message = 'Nama dan kelas wajib diisi.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        if gender not in {'Laki-laki', 'Perempuan'}:
            message = 'Jenis kelamin wajib dipilih.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        if not birth_place or not birth_date_raw or not religion or not address:
            message = 'Tempat lahir, tanggal lahir, agama, dan alamat wajib diisi.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        try:
            birth_date = datetime.strptime(birth_date_raw, '%Y-%m-%d').date()
        except ValueError:
            message = 'Format tanggal lahir tidak valid.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        if 'photos' not in request.files:
            message = 'Foto belum diupload.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        files = request.files.getlist('photos')

        if not files or files[0].filename == '':
            message = 'Tidak ada foto yang dipilih.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        if len(files) > 10:
            message = 'Maksimal 10 foto per siswa.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        # Validate files
        valid_files = []
        for file in files:
            if not file or not file.filename:
                continue
            if not allowed_file(file.filename):
                continue
            try:
                image = Image.open(file.stream)
                image.verify()
            except Exception:
                continue
            finally:
                try:
                    file.stream.seek(0)
                except Exception:
                    pass
            valid_files.append(file)

        if len(valid_files) == 0:
            message = 'Tidak ada foto valid (JPG/PNG dan file gambar yang benar).'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

        student_folder = Path(current_app.config['DATA_FOLDER']) / 'students' / student_id
        student_folder.mkdir(parents=True, exist_ok=True)

        encodings = []
        saved_photos = []

        # Process photos
        for i, photo_file in enumerate(valid_files):
            filename = secure_filename(f'photo_{i+1}.jpg')
            filepath = student_folder / filename
            photo_file.save(str(filepath))
            saved_photos.append(str(filepath))

            if RECOGNITION_ENABLED:
                try:
                    image = face_recognition.load_image_file(str(filepath))
                    face_locations = face_recognition.face_locations(image)
                    face_encodings_list = face_recognition.face_encodings(image, face_locations)

                    if len(face_encodings_list) > 0:
                        encodings.append(face_encodings_list[0])
                except Exception as e:
                    current_app.logger.error(f'Error processing photo for encoding: {e}')

        # Warning if no encodings found but photos saved
        if len(encodings) == 0 and RECOGNITION_ENABLED:
             current_app.logger.warning(f'No face encodings found for student {student_id}')
        
        # Create student record in database
        student = Student(
            student_id=student_id,
            name=name,
            class_name=class_name,
            gender=gender,
            birth_place=birth_place,
            birth_date=birth_date,
            religion=religion,
            address=address,
            added_date=date.today()
        )
        student.set_photos(saved_photos)
        
        if len(encodings) > 0:
            student.set_face_encodings(encodings)

        try:
            db.session.add(student)
            db.session.commit()
            
            if RECOGNITION_ENABLED:
                if len(encodings) > 0:
                    message = f'Berhasil menambahkan {name} dengan {len(encodings)} encoding wajah.'
                else:
                    message = f'Berhasil menambahkan {name} (Tanpa deteksi wajah - foto mungkin tidak jelas).'
            else:
                message = f'Berhasil menambahkan {name} (Mode Tanpa Face Recognition).'
            
            current_app.logger.info(f'Added student: {student_id} - {name}')
            
            # Sync face cache
            FaceCache.sync()
            
            if wants_json:
                return jsonify({'success': True, 'message': message})
            flash(message, 'success')
            return redirect(url_for('students.students'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding student: {e}')
            message = 'Terjadi kesalahan saat menyimpan data siswa.'
            if wants_json:
                return jsonify({'success': False, 'message': message})
            flash(message, 'error')
            return redirect(url_for('students.add_student'))

    # Need to check if CAMERA_ENABLED needs to be imported, but template uses recognition_enabled mainly
    # Add student template might use camera, so let's import CAMERA_ENABLED from camera_service if needed, 
    # but add_student template in this project seems to handle camera in frontend or via simple file upload mostly.
    # Actually, add_student.html might use camera. Let's check imports.
    # Camera logic is in frontend JS usually, but if template needs a flag:
    from app.services.camera_service import CAMERA_ENABLED
    
    return render_template('add_student.html', 
                          camera_enabled=CAMERA_ENABLED, 
                          recognition_enabled=RECOGNITION_ENABLED)

@students_bp.route('/bulk_upload', methods=['GET', 'POST'])
@admin_required
def bulk_upload():
    """Bulk upload students from CSV"""
    results = None
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('File tidak ditemukan.', 'error')
            return redirect(url_for('students.bulk_upload'))
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('Tidak ada file yang dipilih.', 'error')
            return redirect(url_for('students.bulk_upload'))
        
        if not file.filename.endswith('.csv'):
            flash('File harus berformat CSV.', 'error')
            return redirect(url_for('students.bulk_upload'))
        
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        
        results = {'total': 0, 'success': 0, 'failed': 0, 'errors': []}
        
        required_fields = [
            'student_id',
            'name',
            'class_name',
            'gender',
            'birth_place',
            'birth_date',
            'religion',
            'address'
        ]
        if not all(field in reader.fieldnames for field in required_fields):
            flash(f"CSV harus memiliki kolom: {', '.join(required_fields)}", 'error')
            return redirect(url_for('students.bulk_upload'))

        for i, row in enumerate(reader):
            results['total'] += 1
            student_id = (row.get('student_id') or '').strip()
            name = (row.get('name') or '').strip()
            class_name = (row.get('class_name') or '').strip()
            gender = (row.get('gender') or '').strip()
            birth_place = (row.get('birth_place') or '').strip()
            birth_date_raw = (row.get('birth_date') or '').strip()
            religion = (row.get('religion') or '').strip()
            address = (row.get('address') or '').strip()

            if not student_id or not name or not class_name or not gender or not birth_place or not birth_date_raw or not religion or not address:
                results['failed'] += 1
                results['errors'].append({'row': i+2, 'msg': 'Field tidak boleh kosong'})
                continue

            if not is_valid_nisn(student_id):
                results['failed'] += 1
                results['errors'].append({'row': i+2, 'msg': 'NISN harus 10 digit angka'})
                continue

            if gender not in {'Laki-laki', 'Perempuan'}:
                results['failed'] += 1
                results['errors'].append({'row': i+2, 'msg': 'Jenis kelamin harus Laki-laki/Perempuan'})
                continue

            try:
                birth_date = datetime.strptime(birth_date_raw, '%Y-%m-%d').date()
            except ValueError:
                results['failed'] += 1
                results['errors'].append({'row': i+2, 'msg': 'Tanggal lahir harus format YYYY-MM-DD'})
                continue

            if Student.query.filter_by(student_id=student_id).first():
                results['failed'] += 1
                results['errors'].append({'row': i+2, 'msg': 'ID sudah terdaftar'})
                continue

            try:
                student = Student(
                    student_id=student_id,
                    name=name,
                    class_name=class_name,
                    gender=gender,
                    birth_place=birth_place,
                    birth_date=birth_date,
                    religion=religion,
                    address=address,
                    added_date=date.today()
                )
                db.session.add(student)
                results['success'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({'row': i+2, 'msg': str(e)})

        try:
            db.session.commit()
            
            # Sync face cache
            FaceCache.sync()
            
            flash(f"Impor selesai. {results['success']} siswa ditambahkan.", 'success')
        except Exception as e:
            db.session.rollback()
            flash('Terjadi kesalahan saat menyimpan ke database.', 'error')

    return render_template('bulk_upload.html', results=results)

@students_bp.route('/download_template')
@admin_required
def download_template():
    """Download CSV Template for Bulk Upload"""
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['student_id', 'name', 'class_name', 'gender', 'birth_place', 'birth_date', 'religion', 'address'])
    cw.writerow(['1234567890', 'Budi Santoso', 'XII-RPL-1', 'Laki-laki', 'Mataram', '2007-01-12', 'Islam', 'Jl. Pendidikan No. 1'])
    cw.writerow(['1234567891', 'Siti Aminah', 'XII-TKJ-2', 'Perempuan', 'Lombok Utara', '2007-02-20', 'Islam', 'Jl. Sekolah No. 2'])
    
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='template_siswa.csv',
        mimetype='text/csv'
    )

@students_bp.route('/edit_student/<student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    """Edit student details and photos"""
    student = Student.query.filter_by(student_id=student_id).first()
    
    if not student:
        flash('Siswa tidak ditemukan.', 'error')
        return redirect(url_for('students.students'))

    current_photos = student.get_photos()

    if request.method == 'POST':
        # Handle Photo Deletion
        delete_photo = request.form.get('delete_photo')
        if delete_photo:
            if delete_photo in current_photos:
                try:
                    p = Path(delete_photo)
                    if p.exists():
                        p.unlink()
                    
                    new_photos = [ph for ph in current_photos if ph != delete_photo]
                    student.set_photos(new_photos)
                    
                    if RECOGNITION_ENABLED:
                        encodings = []
                        for ph in new_photos:
                            try:
                                image = face_recognition.load_image_file(ph)
                                fe = face_recognition.face_encodings(image)
                                if fe: encodings.append(fe[0])
                            except: pass
                        student.set_face_encodings(encodings)
                    
                    db.session.commit()
                    FaceCache.sync()
                    flash('Foto berhasil dihapus.', 'success')
                except Exception as e:
                    current_app.logger.error(f"Error deleting photo: {e}")
                    flash('Gagal menghapus foto.', 'error')
            return redirect(url_for('students.edit_student', student_id=student.student_id))

        # Handle Main Data Update
        new_student_id = (request.form.get('student_id') or '').strip()
        new_name = (request.form.get('name') or '').strip()
        new_class_name = (request.form.get('class_name') or '').strip()
        new_gender = (request.form.get('gender') or '').strip()
        new_birth_place = (request.form.get('birth_place') or '').strip()
        new_birth_date_raw = (request.form.get('birth_date') or '').strip()
        new_religion = (request.form.get('religion') or '').strip()
        new_address = (request.form.get('address') or '').strip()

        if not is_valid_nisn(new_student_id):
            flash('NISN/Identification ID harus 10 digit angka.', 'error')
            return redirect(url_for('students.edit_student', student_id=student_id))

        if new_student_id != student.student_id and Student.query.filter_by(student_id=new_student_id).first():
            flash('ID sudah dipakai.', 'error')
            return redirect(url_for('students.edit_student', student_id=student_id))

        if new_gender not in {'Laki-laki', 'Perempuan'}:
            flash('Jenis kelamin wajib dipilih.', 'error')
            return redirect(url_for('students.edit_student', student_id=student_id))

        if not new_birth_place or not new_birth_date_raw or not new_religion or not new_address:
            flash('Tempat lahir, tanggal lahir, agama, dan alamat wajib diisi.', 'error')
            return redirect(url_for('students.edit_student', student_id=student_id))

        try:
            new_birth_date = datetime.strptime(new_birth_date_raw, '%Y-%m-%d').date()
        except ValueError:
            flash('Format tanggal lahir tidak valid.', 'error')
            return redirect(url_for('students.edit_student', student_id=student_id))

        try:
            if 'new_photos' in request.files:
                files = request.files.getlist('new_photos')
                student_folder = Path(current_app.config['DATA_FOLDER']) / 'students' / student.student_id
                student_folder.mkdir(parents=True, exist_ok=True)
                
                new_paths = []
                for i, f in enumerate(files):
                    if f and allowed_file(f.filename):
                        fname = f"added_{datetime.now().timestamp()}_{i}.jpg"
                        fpath = student_folder / fname
                        f.save(str(fpath))
                        new_paths.append(str(fpath))
                
                if new_paths:
                    updated_photos = current_photos + new_paths
                    student.set_photos(updated_photos)
                    
                    if RECOGNITION_ENABLED:
                        encodings = student.get_face_encodings()
                        for ph in new_paths:
                            try:
                                img = face_recognition.load_image_file(ph)
                                fe = face_recognition.face_encodings(img)
                                if fe: encodings.append(fe[0])
                            except: pass
                        student.set_face_encodings(encodings)

            if new_student_id != student.student_id:
                old_folder = Path(current_app.config['DATA_FOLDER']) / 'students' / student.student_id
                new_folder = Path(current_app.config['DATA_FOLDER']) / 'students' / new_student_id
                if old_folder.exists():
                    old_folder.rename(new_folder)
                
                updated_photos = [p.replace(str(old_folder), str(new_folder)) for p in student.get_photos()]
                student.set_photos(updated_photos)
                student.student_id = new_student_id

            student.name = new_name
            student.class_name = new_class_name
            student.gender = new_gender
            student.birth_place = new_birth_place
            student.birth_date = new_birth_date
            student.religion = new_religion
            student.address = new_address
            db.session.commit()
            FaceCache.sync()
            flash('Data berhasil diperbarui.', 'success')
            return redirect(url_for('students.students'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Edit error: {e}")
            flash('Terjadi kesalahan.', 'error')

    return render_template('edit_student.html', student=student, photos=current_photos)

@students_bp.route('/delete_student/<student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    """Delete student with option to remove photos"""
    student = Student.query.filter_by(student_id=student_id).first()

    if not student:
        flash('Siswa tidak ditemukan.', 'error')
        return redirect(url_for('students.students'))

    # Check if we should delete photos (hard delete) or just deactivate (soft delete)
    delete_photos = request.form.get('delete_photos') == 'true'

    try:
        student_name = student.name
        
        if delete_photos:
            # Hard delete: Remove student and all photos
            student_folder = Path(current_app.config['DATA_FOLDER']) / 'students' / student_id
            if student_folder.exists():
                try:
                    shutil.rmtree(student_folder)
                    current_app.logger.info(f'Removed student folder: {student_folder}')
                except Exception as e:
                    current_app.logger.error(f'Error removing student folder: {e}')
                    flash(f'Gagal menghapus folder foto: {e}', 'warning')
            
            # Delete from database
            db.session.delete(student)
            flash(f'Berhasil menghapus {student_name} dan semua foto.', 'success')
            current_app.logger.info(f'Hard deleted student: {student_id} - {student_name}')
        else:
            # Soft delete: Just mark as inactive
            student.is_active = False
            flash(f'Berhasil menonaktifkan {student_name}. Foto masih tersimpan.', 'success')
            current_app.logger.info(f'Soft deleted (deactivated) student: {student_id} - {student_name}')
        
        db.session.commit()
        FaceCache.sync()
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting student: {e}')
        flash('Terjadi kesalahan saat menghapus siswa.', 'error')

    return redirect(url_for('students.students'))


@students_bp.route('/hard_delete_student/<student_id>', methods=['POST'])
@admin_required
def hard_delete_student(student_id):
    """Permanently delete student and all associated photos"""
    student = Student.query.filter_by(student_id=student_id).first()

    if not student:
        flash('Siswa tidak ditemukan.', 'error')
        return redirect(url_for('students.students'))

    try:
        # Delete student folder with all photos
        student_folder = Path(current_app.config['DATA_FOLDER']) / 'students' / student_id
        if student_folder.exists():
            shutil.rmtree(student_folder)
            current_app.logger.info(f'Removed student folder: {student_folder}')

        # Delete from database
        db.session.delete(student)
        db.session.commit()
        
        flash(f'Berhasil menghapus {student.name} dan semua foto secara permanen.', 'success')
        current_app.logger.info(f'Hard deleted student: {student_id} - {student.name}')
        FaceCache.sync()
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error hard deleting student: {e}')
        flash('Terjadi kesalahan saat menghapus siswa.', 'error')

    return redirect(url_for('students.students'))

@students_bp.route('/data/students/<path:filename>')
@admin_required
def serve_student_photo(filename):
    """Serve student photos from data directory"""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in current_app.config.get('ALLOWED_EXTENSIONS', set()):
        abort(404)

    students_dir = Path(current_app.config['DATA_FOLDER']) / 'students'
    return send_from_directory(str(students_dir), filename)
