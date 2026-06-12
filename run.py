from app import create_app

app = create_app()

if __name__ == '__main__':
    school_name = app.config.get('SCHOOL_NAME', 'SMA N 1 KAYANGAN')
    print("="*70)
    print(" WEB-BASED FACE RECOGNITION ATTENDANCE SYSTEM v2.0 (Refactored)")
    print(f" Institution: {school_name}")
    print("="*70)
    print("\n🔒 Security Features:")
    print("  ✓ Password protection")
    print("  ✓ CSRF protection enabled")
    print("  ✓ Session security")
    print("  ✓ Structured logging")
    print("\n💾 Database:")
    print(f"  ✓ SQLite: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("\nStarting server...")
    print(f"Access the application at: http://{app.config['HOST']}:{app.config['PORT']}")
    if app.config.get('ENABLE_CONFIG_ADMIN_LOGIN', False):
        print("\n⚠ Config-based admin login fallback is ENABLED.")
    else:
        print("\n👤 Login menggunakan akun admin di database.")
    print("\nPress CTRL+C to stop the server")
    print("="*70)
    
    app.run(
        debug=app.config['FLASK_DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT']
    )
