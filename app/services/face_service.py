try:
    import face_recognition
except ImportError:
    face_recognition = None
from datetime import datetime, timedelta
from app.models.models import Student
from flask import current_app

class FaceCache:
    """Caching for face encodings with TTL auto-expire to improve performance"""
    _known_encodings = []
    _known_names = []
    _student_map = {}
    _last_sync = None
    _cache_ttl_seconds = 300  # 5 minutes default TTL

    @classmethod
    def set_ttl(cls, seconds):
        """Set cache TTL in seconds"""
        cls._cache_ttl_seconds = max(60, seconds)  # Minimum 1 minute

    @classmethod
    def is_cache_expired(cls):
        """Check if cache has expired"""
        if cls._last_sync is None:
            return True
        elapsed = (datetime.now() - cls._last_sync).total_seconds()
        return elapsed > cls._cache_ttl_seconds

    @classmethod
    def invalidate(cls):
        """Manually invalidate cache"""
        cls._known_encodings = []
        cls._known_names = []
        cls._student_map = {}
        cls._last_sync = None

    @classmethod
    def sync(cls):
        """Synchronize cache with database"""
        try:
            # Need application context if called outside request
            students = Student.query.filter_by(is_active=True).all()
            new_encodings = []
            new_names = []
            new_map = {}

            for student in students:
                encs = student.get_face_encodings()
                for e in encs:
                    new_encodings.append(e)
                    new_names.append(student.student_id)

                new_map[student.student_id] = {
                    'name': student.name,
                    'class_name': student.class_name
                }

            cls._known_encodings = new_encodings
            cls._known_names = new_names
            cls._student_map = new_map
            cls._last_sync = datetime.now()
            current_app.logger.info(f"Face cache synced: {len(new_encodings)} encodings, {len(new_map)} students loaded. TTL: {cls._cache_ttl_seconds}s")
        except Exception as e:
            current_app.logger.error(f"Error syncing face cache: {e}")

    @classmethod
    def get_data(cls):
        """Get cached encodings and names, auto-refresh if expired"""
        if cls.is_cache_expired():
            if cls._last_sync is not None:
                current_app.logger.info("Face cache expired, refreshing...")
            cls.sync()
        return cls._known_encodings, cls._known_names

    @classmethod
    def get_student_details(cls, student_id):
        """Get student details from cache"""
        if cls._last_sync is None or cls.is_cache_expired():
            cls.sync()
        return cls._student_map.get(student_id)

    @classmethod
    def get_cache_stats(cls):
        """Get cache statistics for monitoring"""
        return {
            'is_cached': cls._last_sync is not None,
            'last_sync': cls._last_sync.isoformat() if cls._last_sync else None,
            'ttl_seconds': cls._cache_ttl_seconds,
            'is_expired': cls.is_cache_expired(),
            'encoding_count': len(cls._known_encodings),
            'student_count': len(cls._student_map)
        }

def load_face_encodings():
    """Load face encodings (now using cache with TTL)"""
    return FaceCache.get_data()
