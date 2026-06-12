from flask import Blueprint, render_template, Response, request, jsonify, current_app
from app.services.camera_service import gen_frames, CAMERA_ENABLED, RECOGNITION_ENABLED
from app.services.face_service import load_face_encodings
from app.services.rate_limit_service import RateLimiter, get_client_ip
from app.models.models import db, Student, Attendance, get_setting
try:
    import face_recognition
except ImportError:
    face_recognition = None
import base64
from io import BytesIO
from PIL import Image
import numpy as np
try:
    import cv2
except ImportError:
    cv2 = None
from datetime import date, datetime, timedelta

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance')
def attendance_page():
    """Attendance tracking page"""
    return render_template('attendance.html',
                          camera_enabled=CAMERA_ENABLED,
                          recognition_enabled=RECOGNITION_ENABLED)

@attendance_bp.route('/video_feed')
def video_feed():
    """Video streaming route"""
    if not CAMERA_ENABLED:
        return Response('Kamera belum tersedia di environment ini.', 
                       status=503, mimetype='text/plain')
    return Response(gen_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@attendance_bp.route('/mark_attendance', methods=['POST'])
def mark_attendance_api():
    """API to mark attendance from webcam"""
    try:
        client_ip = get_client_ip(request)
        attempts = current_app.config.get('ATTENDANCE_RATE_LIMIT_ATTEMPTS', 30)
        window = current_app.config.get('ATTENDANCE_RATE_LIMIT_WINDOW_SECONDS', 60)
        allowed, retry_after = RateLimiter.check(f'attendance:{client_ip}', attempts, window)
        if not allowed:
            return jsonify({
                'success': False,
                'message': f'Terlalu banyak request. Coba lagi dalam {retry_after} detik.',
                'retry_after': retry_after
            }), 429, {'Retry-After': str(retry_after)}

        attendance_flag = get_setting('attendance_enabled', 'true')
        if isinstance(attendance_flag, str):
            attendance_flag = attendance_flag.lower() == 'true'
        if not attendance_flag:
            return jsonify({
                'success': False,
                'message': 'Absensi otomatis sedang dinonaktifkan di menu Pengaturan.'
            })

        if not RECOGNITION_ENABLED:
            return jsonify({
                'success': False, 
                'message': 'Fitur face recognition belum tersedia di environment ini.'
            })

        # Load encodings
        known_encodings, known_names = load_face_encodings()
        
        if len(known_encodings) == 0:
            return jsonify({'success': False, 'message': 'Belum ada siswa terdaftar.'})

        data = request.get_json(silent=True) or {}
        image_data = data.get('image')
        
        if not isinstance(image_data, str) or not image_data.strip():
            return jsonify({'success': False, 'message': 'Image tidak valid.'})

        if ',' in image_data:
            _, image_data = image_data.split(',', 1)

        try:
            decoded = base64.b64decode(image_data, validate=True)
        except Exception:
            return jsonify({'success': False, 'message': 'Image base64 tidak valid.'})

        try:
            image = Image.open(BytesIO(decoded)).convert('RGB')
        except Exception:
            return jsonify({'success': False, 'message': 'File gambar tidak bisa dibaca.'})

        rgb_image = np.array(image)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        face_landmarks_list = face_recognition.face_landmarks(rgb_image, face_locations)

        if len(face_encodings) == 0:
            return jsonify({'success': False, 'message': 'Tidak ada wajah terdeteksi.'})

        marked = []
        errors = []

        for face_encoding, face_landmarks, face_loc in zip(face_encodings, face_landmarks_list, face_locations):
            top, right, bottom, left = face_loc
            face_height = bottom - top

            # Per-face quality and anti-spoofing checks
            if face_height < 80:
                errors.append('Wajah terlalu jauh atau tidak jelas, dekati kamera.')
                continue

            if cv2 is not None:
                face_roi = rgb_image[top:bottom, left:right]
                gray = cv2.cvtColor(face_roi, cv2.COLOR_RGB2GRAY)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                if laplacian_var < 40:
                    errors.append('Kualitas gambar rendah, pastikan pencahayaan cukup.')
                    continue
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                if hist[0] + hist[255] > (gray.size * 0.1):
                    errors.append('Terdeteksi pantulan layar atau cahaya berlebih.')
                    continue

            matches = face_recognition.compare_faces(
                known_encodings,
                face_encoding,
                tolerance=current_app.config['FACE_RECOGNITION_TOLERANCE']
            )

            if len(known_encodings) > 0:
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        student_id = known_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]
                        
                        # Check if already marked today
                        today = date.today()
                        now_time = datetime.now().time()
                        
                        # Determine Session & Status
                        session_type = 'morning'
                        status = 'Present'
                        
                        m_start = datetime.strptime(get_setting('morning_session_start', '07:00'), '%H:%M').time()
                        m_end = datetime.strptime(get_setting('morning_session_end', '12:00'), '%H:%M').time()
                        a_start = datetime.strptime(get_setting('afternoon_session_start', '13:00'), '%H:%M').time()
                        a_end = datetime.strptime(get_setting('afternoon_session_end', '17:00'), '%H:%M').time()
                        late_threshold = int(get_setting('late_threshold_minutes', '15'))

                        if now_time >= a_start:
                            session_type = 'afternoon'
                            late_time = (datetime.combine(today, a_start) + timedelta(minutes=late_threshold)).time()
                            if now_time > late_time:
                                status = 'Late'
                        else:
                            session_type = 'morning'
                            late_time = (datetime.combine(today, m_start) + timedelta(minutes=late_threshold)).time()
                            if now_time > late_time:
                                status = 'Late'

                        existing = Attendance.query.filter_by(
                            student_id=student_id,
                            date=today,
                            session_type=session_type
                        ).first()

                        if existing:
                            errors.append(f"{student_id} sudah absen {session_type} hari ini.")
                            continue

                        # Create attendance record
                        student = Student.query.filter_by(student_id=student_id).first()
                        if student:
                            attendance = Attendance(
                                student_id=student_id,
                                date=today,
                                time=now_time,
                                status=status,
                                session_type=session_type,
                                confidence=float(confidence),
                                marked_by='auto'
                            )
                            db.session.add(attendance)
                            marked.append(student.name)

        if marked:
            try:
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': f'Berhasil absen: {", ".join(marked)}',
                    'marked': marked
                })
            except Exception as db_error:
                db.session.rollback()
                # Handle unique constraint violation
                if 'UNIQUE constraint' in str(db_error) or 'uq_student_date_session' in str(db_error):
                    current_app.logger.warning(f'Duplicate attendance attempt blocked: {db_error}')
                    return jsonify({
                        'success': False,
                        'message': 'Siswa sudah absen untuk sesi ini hari ini.'
                    })
                # Other database error
                current_app.logger.error(f'Database error during attendance commit: {db_error}')
                return jsonify({
                    'success': False,
                    'message': 'Terjadi kesalahan database, silakan coba lagi.'
                })
        
        if errors:
            return jsonify({'success': False, 'message': errors[0]})

        return jsonify({'success': False, 'message': 'Wajah tidak dikenali.'})

    except Exception as e:
        current_app.logger.exception('mark_attendance_api_failed')
        return jsonify({'success': False, 'message': 'Terjadi kesalahan server, silakan coba lagi.'})
