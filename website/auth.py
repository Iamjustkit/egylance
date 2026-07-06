from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from .i18n import get_lang, get_translations
from .models import authenticate_user, create_user

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


@auth.route('/auth/google')
def google_auth():
    flash('Google sign-in will be enabled once Google OAuth credentials are configured.', 'info')
    return redirect(url_for('auth.signup'))


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
