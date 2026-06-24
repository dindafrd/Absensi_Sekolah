"""Compatibility launcher.

Use `python run.py` as the primary entrypoint.
This file is kept so `python app.py` still works.
"""

from app import create_app

app = create_app()


if __name__ == '__main__':
    print("[INFO] `python app.py` is deprecated. Prefer `python run.py`.")
    app.run(
        debug=app.config['FLASK_DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT'],
    )
