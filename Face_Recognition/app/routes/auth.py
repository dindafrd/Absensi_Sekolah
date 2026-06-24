from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from app.utils.password import validate_password_strength, get_password_requirements
import bcrypt
from datetime import datetime
from app.models.models import User, db
from app.services.rate_limit_service import RateLimiter, get_client_ip
from app.routes.main import admin_required

auth_bp = Blueprint('auth', __name__)


def _set_authenticated_session(username, role='admin', user_id=None, auth_source='database'):
    """Persist a consistent authenticated session context."""
    session.clear()
    session['is_admin'] = role == 'admin'
    session['username'] = username
    session['role'] = role
    session['auth_source'] = auth_source
    if user_id is not None:
        session['user_id'] = user_id
    session.permanent = True

def get_safe_next_url():
    """Get safe redirect URL"""
    next_url = request.args.get('next')
    if not next_url:
        return None
    if next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        client_ip = get_client_ip(request)
        username = (request.form.get('username') or '').strip().lower()
        attempts = current_app.config.get('LOGIN_RATE_LIMIT_ATTEMPTS', 5)
        window = current_app.config.get('LOGIN_RATE_LIMIT_WINDOW_SECONDS', 60)
        checks = [RateLimiter.check(f'login:ip:{client_ip}', attempts, window)]
        if username:
            checks.append(RateLimiter.check(f'login:user:{username}', attempts, window))

        limited = [(allowed, retry_after) for allowed, retry_after in checks if not allowed]
        if limited:
            retry_after = max(item[1] for item in limited)
            flash(f'Terlalu banyak percobaan login. Coba lagi dalam {retry_after} detik.', 'error')
            current_app.logger.warning(f'Login rate limited for ip={client_ip}, username={username or "<empty>"}')
            return render_template('login.html'), 429, {'Retry-After': str(retry_after)}

        password = (request.form.get('password') or '').strip()
        
        # 1. Try finding user in database
        user = User.query.filter_by(username=username).first()
        
        is_match = False
        if user and user.password_hash:
            is_match = check_password_hash(user.password_hash, password)
        elif username == 'admin' and current_app.config.get('ENABLE_CONFIG_ADMIN_LOGIN', False):
            # Optional fallback path for emergency recovery only.
            configured_password = (current_app.config.get('ADMIN_PASSWORD') or '').strip()
            if configured_password:
                if configured_password.startswith('$2b$'):
                    try:
                        is_match = bcrypt.checkpw(password.encode(), configured_password.encode())
                    except Exception:
                        is_match = False
                else:
                    is_match = (password == configured_password)

        if is_match:
            auth_source = 'database' if user else 'config_fallback'
            role = getattr(user, 'role', 'admin') or 'admin'
            _set_authenticated_session(
                username=username,
                role=role,
                user_id=getattr(user, 'id', None),
                auth_source=auth_source,
            )
            # Update last login if db user
            if user:
                user.last_login = datetime.utcnow()
                db.session.commit()
                
            flash('Login berhasil.', 'success')
            current_app.logger.info(f'Login successful for {username}')
            return redirect(get_safe_next_url() or url_for('main.index'))

        flash('Username atau Password salah.', 'error')
        current_app.logger.warning(f'Failed login attempt for {username}')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Logout berhasil.', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@admin_required
def change_password():
    """Change password page with strength validation"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Verify current password
        username = session.get('username', '').lower()
        auth_source = session.get('auth_source', 'database')
        if auth_source != 'database':
            flash('Password akun fallback konfigurasi tidak dapat diubah dari aplikasi.', 'error')
            return render_template('change_password.html',
                                 requirements=get_password_requirements())

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, current_password):
            flash('Password saat ini salah', 'error')
            return render_template('change_password.html', 
                                 requirements=get_password_requirements())

        # Check if passwords match
        if new_password != confirm_password:
            flash('Password baru dan konfirmasi tidak cocok', 'error')
            return render_template('change_password.html',
                                 requirements=get_password_requirements())

        # Validate password strength
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('change_password.html',
                                 requirements=get_password_requirements())

        # Update password
        try:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Password berhasil diubah', 'success')
            current_app.logger.info(f'Password changed for user {username}')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error changing password: {e}')
            flash('Terjadi kesalahan saat mengubah password', 'error')

    return render_template('change_password.html',
                         requirements=get_password_requirements())


@auth_bp.route('/api/validate_password', methods=['POST'])
def api_validate_password():
    """API endpoint to validate password strength in real-time"""
    data = request.get_json()
    password = data.get('password', '')
    
    is_valid, error_msg = validate_password_strength(password)
    return jsonify({
        'valid': is_valid,
        'message': error_msg if error_msg else 'Password memenuhi persyaratan'
    })
