import os
from flask import Flask
from .models import init_db, ensure_default_admin


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'egylance-super-secret-key-2026'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'verifications')
    os.makedirs(upload_dir, exist_ok=True)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    init_db()
    ensure_default_admin()
    return app
