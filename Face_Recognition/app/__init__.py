from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from app.config import get_config
from app.models.models import db, init_db
from app.services.database import init_database_directories
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import json
from datetime import datetime

csrf = CSRFProtect()
migrate = Migrate(compare_type=True)


class StructuredFormatter(logging.Formatter):
    """JSON structured logging formatter for better log analysis"""
    
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add custom attributes if available (use getattr for type safety)
        request_id = getattr(record, 'request_id', None)
        if request_id:
            log_entry['request_id'] = request_id
        
        user = getattr(record, 'user', None)
        if user:
            log_entry['user'] = user
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(app):
    """Configure structured logging for the application"""
    
    # Get log level from config
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    
    # Ensure log directory exists
    log_dir = Path('data')
    log_dir.mkdir(exist_ok=True)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        app.config.get('LOG_FILE', 'data/app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    
    # Use structured formatting in production, simple in development
    if app.config.get('FLASK_DEBUG'):
        # Development: Human-readable format
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
    else:
        # Production: JSON structured format
        file_handler.setFormatter(StructuredFormatter())
    
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    ))
    
    # Configure app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    # Log startup message
    app.logger.info('='*60)
    app.logger.info('Face Recognition Attendance System')
    app.logger.info(f'Institution: {app.config.get("SCHOOL_NAME", "Unknown")}')
    app.logger.info(f'Environment: {"Development" if app.debug else "Production"}')
    app.logger.info(f'Database: {app.config.get("SQLALCHEMY_DATABASE_URI", "Not set")}')
    app.logger.info(f'Log Level: {app.config.get("LOG_LEVEL", "INFO")}')
    app.logger.info('='*60)

def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Initialize extensions
    csrf.init_app(app)
    init_db(app)
    migrate.init_app(app, db, directory=str(Path(app.root_path).parent / 'migrations'))
    init_database_directories()

    # Setup enhanced logging
    setup_logging(app)
    
    if app.config.get('RUN_STARTUP_TASKS', True):
        # Perform automatic database backup on startup
        try:
            from app.services.database import auto_backup_database
            app.logger.info('Performing automatic database backup...')
            if auto_backup_database():
                app.logger.info('Automatic database backup completed')
            else:
                app.logger.warning('Automatic database backup skipped or failed')
        except Exception as e:
            app.logger.warning(f'Auto backup failed on startup (non-critical): {e}')
        
    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.students import students_bp
    from app.routes.attendance import attendance_bp
    from app.routes.reports import reports_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    
    # Inject context
    from datetime import datetime
    @app.context_processor
    def inject_now():
        return {
            'now': datetime.now(),
            'school_name': app.config.get('SCHOOL_NAME', 'SMA N 1 KAYANGAN')
        }
        
    return app
