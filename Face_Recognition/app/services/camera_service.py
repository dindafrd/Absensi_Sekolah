try:
    import cv2
except ImportError:
    cv2 = None
import numpy as np
import os
try:
    import face_recognition
except ImportError:
    face_recognition = None
from flask import current_app
from app.services.face_service import load_face_encodings, FaceCache
import atexit
import time

# Global variables for camera
camera = None
CAMERA_ENABLED = cv2 is not None
RECOGNITION_ENABLED = face_recognition is not None

def release_camera():
    """Release camera resources"""
    global camera
    if camera is not None:
        try:
            camera.release()
        finally:
            camera = None

atexit.register(release_camera)

def gen_frames():
    """Generator function for video streaming"""
    global camera
    if not CAMERA_ENABLED:
        return

    def yield_placeholder_frame(message):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, message, (14, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            return
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def open_camera():
        global camera
        if camera is not None and camera.isOpened():
            return camera

        release_camera()

        indices_env = os.environ.get('CAMERA_INDEX', '').strip()
        indices = []
        if indices_env:
            for part in indices_env.split(','):
                part = part.strip()
                if part.isdigit():
                    indices.append(int(part))
        if not indices:
            indices = [0, 1, 2, 3]

        cap_dshow = getattr(cv2, 'CAP_DSHOW', None)
        cap_msmf = getattr(cv2, 'CAP_MSMF', None)
        cap_any = getattr(cv2, 'CAP_ANY', None)
        backends = []
        for backend in (cap_dshow, cap_msmf, cap_any):
            if backend is not None and backend not in backends:
                backends.append(backend)
        if not backends:
            backends = [0]

        for idx in indices:
            for backend in backends:
                try:
                    cap = cv2.VideoCapture(idx, backend)
                except Exception:
                    cap = None
                if cap is not None and cap.isOpened():
                    # Set Higher Resolution for better recognition
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    camera = cap
                    return camera
                try:
                    if cap is not None:
                        cap.release()
                except Exception:
                    pass
        return None

    cap = open_camera()
    if cap is None or not cap.isOpened():
        release_camera()
        yield from yield_placeholder_frame('Kamera tidak bisa dibuka')
        return

    try:
        known_encodings, known_names = load_face_encodings()
        frame_count = 0
        process_every_n_frames = int(os.environ.get('PROCESS_EVERY_N_FRAMES', '2'))
        face_model = os.environ.get('FACE_DETECTION_MODEL', 'hog')  # 'hog' (fast) or 'cnn' (accurate)
        max_reconnect = 5

        last_results = []
        fps_start = time.time()
        fps_frame_count = 0
        current_fps = 0.0

        while True:
            success, frame = cap.read()
            if not success:
                # Auto-reconnect on frame read failure
                reconnected = False
                for _ in range(max_reconnect):
                    time.sleep(0.5)
                    cap = open_camera()
                    if cap is not None and cap.isOpened():
                        success, frame = cap.read()
                        if success:
                            reconnected = True
                            break
                if not reconnected:
                    yield from yield_placeholder_frame('Kamera terputus. Silakan refresh halaman.')
                    break

            # FPS tracking
            fps_frame_count += 1
            elapsed = time.time() - fps_start
            if elapsed >= 1.0:
                current_fps = fps_frame_count / elapsed
                fps_frame_count = 0
                fps_start = time.time()

            frame_count += 1

            if RECOGNITION_ENABLED and len(known_encodings) > 0:
                if frame_count % process_every_n_frames == 0:
                    # Scale down for faster processing (0.25x = 4x speed)
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                    face_locs = face_recognition.face_locations(rgb_small_frame, model=face_model)
                    face_encs = face_recognition.face_encodings(
                        rgb_small_frame, face_locs, num_jitters=1
                    )

                    last_results = []
                    for (top, right, bottom, left), face_encoding in zip(face_locs, face_encs):
                        name = "Unknown"
                        confidence_score = 0.0

                        matches = face_recognition.compare_faces(
                            known_encodings,
                            face_encoding,
                            tolerance=current_app.config['FACE_RECOGNITION_TOLERANCE']
                        )
                        face_distances = face_recognition.face_distance(known_encodings, face_encoding)

                        if len(face_distances) > 0:
                            best_match_index = int(np.argmin(face_distances))
                            if best_match_index < len(matches) and matches[best_match_index]:
                                student_id = known_names[best_match_index]
                                student_info = FaceCache.get_student_details(student_id)
                                if student_info:
                                    name = student_info['name']
                                    confidence_score = 1.0 - face_distances[best_match_index]

                        # Scale coordinates back to original frame size
                        last_results.append((top * 4, right * 4, bottom * 4, left * 4, name, confidence_score))

            # Draw bounding boxes on every frame using cached last_results
            for (top, right, bottom, left, name, confidence) in last_results:
                color = (94, 197, 34) if name != "Unknown" else (68, 68, 239)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                label = f"{name} ({int(confidence * 100)}%)" if name != "Unknown" else name
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, label, (left + 6, bottom - 6),
                            cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

            # Overlay: FPS and face count (top-left)
            face_count = len(last_results)
            cv2.putText(frame, f'FPS: {current_fps:.1f}', (10, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 0), 2)
            cv2.putText(frame, f'Wajah: {face_count}', (10, 58),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if not ret:
                continue
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    except GeneratorExit:
        # Client disconnected - normal operation
        current_app.logger.info('Camera stream client disconnected')
    except Exception as e:
        current_app.logger.error(f'Camera streaming error: {e}')
        yield from yield_placeholder_frame('Terjadi kesalahan pada kamera')
    finally:
        # Always release camera when generator exits
        release_camera()
        current_app.logger.info('Camera resources released')
