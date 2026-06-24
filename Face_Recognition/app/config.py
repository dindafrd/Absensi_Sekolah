"""
Configuration Management
Centralized configuration with environment variable support
"""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# We are in app/config.py, parent is app/, grandparent is project root
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')


def _generate_secret_key():
    """Generate a secure random secret key if not provided"""
    return secrets.token_hex(32)


class Config:
    """Base configuration"""

    # Flask Core
    # Generate random key if SECRET_KEY not set (better than hardcoded default)
    _provided_secret_key = os.environ.get('SECRET_KEY')
    if _provided_secret_key:
        SECRET_KEY = _provided_secret_key
    else:
        # Auto-generate secure key for development
        SECRET_KEY = _generate_secret_key()
        # Warn in development that secret key will change on restart
        if os.environ.get('FLASK_DEBUG', '1') == '1':
            import warnings
            warnings.warn(
                "SECRET_KEY not set in environment. Auto-generated key will change on each restart. "
                "Set SECRET_KEY in .env file for consistent sessions. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\"",
                RuntimeWarning
            )

    # Debug Mode
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    # Server Configuration
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    SCHOOL_NAME = os.environ.get('SCHOOL_NAME', 'SMA N 1 KAYANGAN')
    
    # Admin Authentication
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
    ENABLE_CONFIG_ADMIN_LOGIN = os.environ.get('ENABLE_CONFIG_ADMIN_LOGIN', '0') == '1'
    
    # Database
    DATABASE_URI = os.environ.get('DATABASE_URI')
    if not DATABASE_URI:
        db_path = basedir / 'data' / 'attendance.db'
        DATABASE_URI = 'sqlite:///' + str(db_path)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    DB_AUTO_CREATE = os.environ.get('DB_AUTO_CREATE', '1') == '1'
    DB_LEGACY_AUTO_REPAIR = os.environ.get('DB_LEGACY_AUTO_REPAIR', '1') == '1'
    
    # Session Security
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # File Upload
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Data Folders
    DATA_FOLDER = 'data'
    STUDENTS_FOLDER = 'data/students'

    # Student ID / NISN Configuration
    # Support 6-10 digits for backward compatibility
    MIN_NISN_LENGTH = int(os.environ.get('MIN_NISN_LENGTH', '6'))
    MAX_NISN_LENGTH = int(os.environ.get('MAX_NISN_LENGTH', '10'))
    
    # Face Recognition
    FACE_RECOGNITION_TOLERANCE = float(os.environ.get('FACE_RECOGNITION_TOLERANCE', '0.6'))
    FACE_DETECTION_MODEL = os.environ.get('FACE_DETECTION_MODEL', 'hog')  # 'hog' or 'cnn'
    
    # WTF Forms (CSRF Protection)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'data/app.log'
    RUN_STARTUP_TASKS = os.environ.get('RUN_STARTUP_TASKS', '1') == '1'

    # Bootstrap Admin
    _auto_create_default_admin = os.environ.get('AUTO_CREATE_DEFAULT_ADMIN')
    if _auto_create_default_admin is None:
        AUTO_CREATE_DEFAULT_ADMIN = FLASK_DEBUG
    else:
        AUTO_CREATE_DEFAULT_ADMIN = _auto_create_default_admin == '1'
    DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin').strip() or 'admin'
    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin1234')

    # Rate Limiting
    LOGIN_RATE_LIMIT_ATTEMPTS = int(os.environ.get('LOGIN_RATE_LIMIT_ATTEMPTS', '5'))
    LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('LOGIN_RATE_LIMIT_WINDOW_SECONDS', '60'))
    ATTENDANCE_RATE_LIMIT_ATTEMPTS = int(os.environ.get('ATTENDANCE_RATE_LIMIT_ATTEMPTS', '30'))
    ATTENDANCE_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('ATTENDANCE_RATE_LIMIT_WINDOW_SECONDS', '60'))


class DevelopmentConfig(Config):
    """Development configuration"""
    FLASK_DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    FLASK_DEBUG = False
    SESSION_COOKIE_SECURE = True
    ENABLE_CONFIG_ADMIN_LOGIN = False
    
    # Override with stronger requirements
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key or key == 'dev-insecure-secret-key-please-change-in-production':
            raise ValueError(
                "SECRET_KEY must be set in production environment. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        return key


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
