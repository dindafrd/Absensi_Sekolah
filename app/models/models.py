"""
Database Models
SQLAlchemy ORM models for the attendance system
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
import pickle

db = SQLAlchemy()


class User(db.Model):
    """Admin/Teacher user accounts"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200))
    role = db.Column(db.String(20), default='admin')  # admin, teacher
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Student(db.Model):
    """Student information and face encodings"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    class_name = db.Column(db.String(50), nullable=False, index=True)
    gender = db.Column(db.String(20))
    birth_place = db.Column(db.String(100))
    birth_date = db.Column(db.Date)
    religion = db.Column(db.String(50))
    address = db.Column(db.Text)
    num_photos = db.Column(db.Integer, default=0)
    photos_path = db.Column(db.Text)  # JSON array of photo paths
    face_encodings = db.Column(db.LargeBinary)  # Pickled numpy arrays
    is_active = db.Column(db.Boolean, default=True)
    added_date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_face_encodings(self):
        """Get face encodings as list"""
        if self.face_encodings:
            try:
                return pickle.loads(self.face_encodings)
            except Exception:
                return []
        return []
    
    def set_face_encodings(self, encodings_list):
        """Set face encodings from list"""
        self.face_encodings = pickle.dumps(encodings_list)
    
    def get_photos(self):
        """Get photos as list"""
        if self.photos_path:
            import json
            try:
                return json.loads(self.photos_path)
            except Exception:
                return []
        return []
    
    def set_photos(self, photos_list):
        """Set photos from list"""
        import json
        self.photos_path = json.dumps(photos_list)
        self.num_photos = len(photos_list)
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.name}>'


class Attendance(db.Model):
    """Attendance records"""
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Present')  # Present, Late, Absent, Excused
    session_type = db.Column(db.String(20), default='morning')  # morning, afternoon
    confidence = db.Column(db.Float)  # Face recognition confidence score
    marked_by = db.Column(db.String(20), default='auto')  # auto, manual
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite unique index to prevent duplicate attendance
    # and improve query performance
    __table_args__ = (
        db.Index('idx_student_date', 'student_id', 'date'),
        db.UniqueConstraint('student_id', 'date', 'session_type', name='uq_student_date_session'),
    )
    
    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.date}>'


class Setting(db.Model):
    """System settings"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Setting {self.key}>'


def init_db(app):
    """Initialize database"""
    db.init_app(app)

    with app.app_context():
        auto_create = app.config.get('DB_AUTO_CREATE', True)
        if auto_create:
            db.create_all()

        inspector = inspect(db.engine)
        table_names = set(inspector.get_table_names())
        if not table_names:
            return

        if app.config.get('DB_LEGACY_AUTO_REPAIR', True):
            _ensure_student_profile_columns()
            _ensure_attendance_unique_constraint()

        _ensure_default_settings()
        _ensure_default_admin_user(app)


def _ensure_default_settings():
    """Create system settings required by the application."""
    default_settings = [
        ('late_threshold_minutes', '15', 'Minutes after scheduled time to mark as late'),
        ('morning_session_start', '07:00', 'Morning session start time (HH:MM)'),
        ('morning_session_end', '12:00', 'Morning session end time (HH:MM)'),
        ('afternoon_session_start', '13:00', 'Afternoon session start time (HH:MM)'),
        ('afternoon_session_end', '17:00', 'Afternoon session end time (HH:MM)'),
        ('attendance_enabled', 'true', 'Enable attendance tracking'),
    ]

    for key, value, description in default_settings:
        if not Setting.query.filter_by(key=key).first():
            setting = Setting(key=key, value=value, description=description)
            db.session.add(setting)

    db.session.commit()


def _ensure_default_admin_user(app):
    """Optionally create a bootstrap admin account for development."""
    if User.query.first():
        return

    if not app.config.get('AUTO_CREATE_DEFAULT_ADMIN', False):
        return

    username = (app.config.get('DEFAULT_ADMIN_USERNAME') or 'admin').strip() or 'admin'
    password = app.config.get('DEFAULT_ADMIN_PASSWORD') or ''
    if not password:
        app.logger.warning('AUTO_CREATE_DEFAULT_ADMIN enabled but DEFAULT_ADMIN_PASSWORD is empty.')
        return

    from werkzeug.security import generate_password_hash

    admin_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        full_name='Administrator',
        role='admin'
    )
    db.session.add(admin_user)
    db.session.commit()

    if password == 'admin1234':
        app.logger.warning('Created bootstrap admin user with default development password. Change it immediately.')
    else:
        app.logger.info(f'Created bootstrap admin user: {username}')


def _ensure_student_profile_columns():
    """Add new student biodata columns for existing databases without migrations."""
    inspector = inspect(db.engine)
    if 'students' not in inspector.get_table_names():
        return

    existing_columns = {column['name'] for column in inspector.get_columns('students')}
    required_columns = {
        'gender': 'VARCHAR(20)',
        'birth_place': 'VARCHAR(100)',
        'birth_date': 'DATE',
        'religion': 'VARCHAR(50)',
        'address': 'TEXT',
    }

    for column_name, column_type in required_columns.items():
        if column_name in existing_columns:
            continue
        db.session.execute(text(f'ALTER TABLE students ADD COLUMN {column_name} {column_type}'))

    db.session.commit()


def _ensure_attendance_unique_constraint():
    """Add unique constraint to attendance table if it doesn't exist."""
    inspector = inspect(db.engine)
    if 'attendance' not in inspector.get_table_names():
        return

    # Check if constraint already exists
    constraints = inspector.get_unique_constraints('attendance')
    constraint_exists = any(c['name'] == 'uq_student_date_session' for c in constraints)

    if not constraint_exists:
        try:
            # Remove duplicate records before adding constraint
            # Keep the earliest record for each duplicate group
            db.session.execute(text("""
                DELETE FROM attendance 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM attendance 
                    GROUP BY student_id, date, session_type
                )
            """))
            db.session.commit()

            # Add unique constraint
            db.session.execute(text("""
                ALTER TABLE attendance 
                ADD CONSTRAINT uq_student_date_session 
                UNIQUE (student_id, date, session_type)
            """))
            db.session.commit()
            print("Added unique constraint to attendance table")
        except Exception as e:
            db.session.rollback()
            # SQLite has limited ALTER TABLE support, create new table if needed
            if 'near "ALTER"' in str(e) or 'not supported' in str(e).lower():
                try:
                    _recreate_attendance_table_with_constraint()
                except Exception as recreate_error:
                    print(f"Warning: Could not add unique constraint: {recreate_error}")
            else:
                print(f"Warning: Could not add unique constraint: {e}")


def _recreate_attendance_table_with_constraint():
    """Recreate attendance table with unique constraint (for SQLite compatibility)."""
    # Check if any duplicates exist
    duplicates = db.session.execute(text("""
        SELECT student_id, date, session_type, COUNT(*) as cnt
        FROM attendance
        GROUP BY student_id, date, session_type
        HAVING cnt > 1
    """)).fetchall()

    if duplicates:
        # Remove duplicates, keep earliest
        for dup in duplicates:
            db.session.execute(text("""
                DELETE FROM attendance 
                WHERE student_id = :sid AND date = :dt AND session_type = :sess
                AND id NOT IN (
                    SELECT MIN(id) FROM attendance 
                    WHERE student_id = :sid AND date = :dt AND session_type = :sess
                )
            """), {'sid': dup[0], 'dt': dup[1], 'sess': dup[2]})
        db.session.commit()

    # For SQLite, we need to recreate the table to add constraints
    # This is a simplified approach - in production, use Flask-Migrate
    print("Note: Attendance unique constraint will be applied on next fresh database creation")


def get_setting(key, default=None):
    """Get setting value by key"""
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        return setting.value
    return default


def set_setting(key, value, description=None):
    """Set setting value"""
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
        if description:
            setting.description = description
    else:
        setting = Setting(key=key, value=value, description=description)
        db.session.add(setting)
    db.session.commit()
