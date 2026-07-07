import os
from flask import Flask, app
from authlib.integrations.flask_client import OAuth
from .models import init_db, ensure_default_admin
from dotenv import load_dotenv
import os

load_dotenv()

oauth = OAuth()

def create_app():
    app = Flask(__name__)

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
    app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")

    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile"
        }
    )

    upload_dir = os.path.join(app.root_path, "static", "uploads", "verifications")
    os.makedirs(upload_dir, exist_ok=True)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    init_db()
    ensure_default_admin()

    return app