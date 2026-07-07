from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from .i18n import get_lang, get_translations
from .models import authenticate_user, create_user
import os
auth = Blueprint('auth', __name__)


def build_context(**kwargs):
    lang = get_lang()
    user = None
    if session.get('user_id'):
        from .models import get_user_by_id
        user = get_user_by_id(session['user_id'])
    return {'lang': lang, 'translations': get_translations(lang), 'user': user, **kwargs}


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        user = authenticate_user(identifier, password)
        if user:
            session['user_id'] = user['id']
            session['lang'] = user['language'] or 'ar'
            flash('Welcome back to EgyLance.', 'success')
            if user['is_admin']:
                return redirect(url_for('views.admin'))
            if user['role'] == 'client':
                return redirect(url_for('views.jobs'))
            return redirect(url_for('views.dashboard'))
        flash('Invalid credentials. Please try again.', 'warning')

    return render_template('login.html', **build_context())


@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('views.home'))

@auth.route("/auth/google")
def google_auth():
    from . import oauth

    google = oauth.create_client("google")
    redirect_uri = url_for("auth.google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@auth.route("/auth/google/callback")
def google_callback():
    from . import oauth
    from .models import get_user_by_email, create_user

    google = oauth.create_client("google")

    token = google.authorize_access_token()

    user_info = token.get("userinfo")
    if user_info is None:
        user_info = google.userinfo()

    email = user_info["email"]
    full_name = user_info.get("name", "")
    google_id = user_info.get("sub")
    username = email.split("@")[0]

    user = get_user_by_email(email)

    if user is None:
        base_username = username
        i = 1

        while get_user_by_email(f"{base_username}{i}@temp.local"):
            i += 1

        user_id = create_user(
            username=username,
            email=email,
            password=os.urandom(32).hex(),
            role="freelancer",
            full_name=full_name,
            google_id=google_id,
            email_verified=1,
        )

        session["user_id"] = user_id
        session["lang"] = "ar"

    else:
        session["user_id"] = user["id"]
        session["lang"] = user["language"]

    flash("Signed in with Google successfully.", "success")
    return redirect(url_for("views.dashboard"))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'freelancer')
        full_name = request.form.get('full_name', '').strip()
        accept_terms = request.form.get('accept_terms') == 'on'
        if not username or not email or not password:
            flash('Please complete all required fields.', 'warning')
            return redirect(url_for('auth.signup'))
        if not accept_terms:
            flash('You must accept the privacy policy and terms of service.', 'warning')
            return redirect(url_for('auth.signup'))
        user_id = create_user(username=username, email=email, password=password, role=role, full_name=full_name)
        if user_id:
            flash('Account created. You can now sign in.', 'success')
            return redirect(url_for('auth.login'))
        flash('That username or email is already in use.', 'warning')

    return render_template('signup.html', **build_context())
