"""
Password validation utilities
"""
import re


def validate_password_strength(password):
    """
    Validate password strength
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, 'Password minimal 8 karakter'
    
    if len(password) > 128:
        return False, 'Password maksimal 128 karakter'
    
    if not re.search(r'[A-Z]', password):
        return False, 'Password harus mengandung minimal satu huruf besar'
    
    if not re.search(r'[a-z]', password):
        return False, 'Password harus mengandung minimal satu huruf kecil'
    
    if not re.search(r'\d', password):
        return False, 'Password harus mengandung minimal satu angka'
    
    # Common passwords check
    common_passwords = [
        'password', '12345678', '123456789', 'qwerty', 'abc123',
        'password123', 'admin123', 'letmein', 'welcome', 'monkey'
    ]
    if password.lower() in common_passwords:
        return False, 'Password terlalu umum, gunakan password yang lebih unik'
    
    return True, ''


def get_password_requirements():
    """Get password requirements list for UI display"""
    return [
        'Minimal 8 karakter',
        'Minimal satu huruf besar (A-Z)',
        'Minimal satu huruf kecil (a-z)',
        'Minimal satu angka (0-9)',
        'Tidak menggunakan password umum'
    ]
