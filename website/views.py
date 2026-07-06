from functools import wraps
import os
from email.message import EmailMessage
import smtplib
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from .i18n import get_lang, get_translations
from .models import (
    create_job,
    create_message,
    create_site_card,
    create_verification_file,
    delete_job,
    delete_user_account,
    get_all_jobs,
    increment_job_view,
    get_all_site_cards,
    get_all_users,
    get_all_verification_requests,
    get_featured_profiles,
    get_job_by_id,
    get_jobs_by_user,
    get_messages_for_job,
    get_profile,
    get_site_cards,
    get_user_by_id,
    get_user_verification_requests,
    get_verification_files,
    increment_user_visit,
    review_verification_request,
    save_client_interest,
    save_profile,
    save_user_language,
    update_user_status,
    update_user_verification,
)

views = Blueprint('views', __name__)


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return view_func(*args, **kwargs)

    return wrapped_view


def send_account_deletion_email(user_email, full_name):
    subject = 'EgyLance account deletion request received'
    body = f"Hello {full_name or user_email},\n\nWe received a request to delete your EgyLance account. If this was not you, please contact support immediately.\n\nRegards,\nEgyLance"
    if os.getenv('MAIL_SERVER'):
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = os.getenv('MAIL_FROM', 'noreply@egylance.local')
        msg['To'] = user_email
        msg.set_content(body)
        try:
            with smtplib.SMTP(os.getenv('MAIL_SERVER', 'localhost'), int(os.getenv('MAIL_PORT', '25'))) as smtp:
                if os.getenv('MAIL_USERNAME'):
                    smtp.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
                smtp.send_message(msg)
            return True
        except Exception:
            return False
    log_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'deletion_requests')
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, f"{user_email.replace('@', '_at_')}.txt"), 'w', encoding='utf-8') as handle:
        handle.write(body)
    return True


def build_context(**kwargs):
    lang = get_lang()
    user = get_user_by_id(session.get('user_id')) if session.get('user_id') else None
    prompt_interest = False
    if user and user['role'] == 'client':
        visit_count = increment_user_visit(user['id'])
        prompt_interest = visit_count % 6 == 0 and not user['looking_for']
    return {
        'lang': lang,
        'translations': get_translations(lang),
        'user': user,
        'prompt_interest': prompt_interest,
        'user_interest': user['looking_for'] if user else None,
        **kwargs,
    }


@views.route('/')
def home():
    services = get_site_cards('services')
    why_cards = get_site_cards('why')
    featured_profiles = get_featured_profiles()
    jobs = get_all_jobs(limit=3)
    return render_template('index.html', services=services, why_cards=why_cards, featured_profiles=featured_profiles, jobs=jobs, **build_context())


@views.route('/search')
def search():
    query = request.args.get('q', '').strip()
    jobs = get_all_jobs(query=query)
    context = build_context(query=query)
    context.update({'jobs': jobs, 'query': query})
    return render_template('search_results.html', **context)


@views.route('/set-language/<lang>')
def set_language(lang):
    if lang not in {'ar', 'en'}:
        lang = 'ar'
    session['lang'] = lang
    if session.get('user_id'):
        save_user_language(session['user_id'], lang)
    return redirect(request.referrer or url_for('views.home'))


@views.route('/dashboard')
@login_required
def dashboard():
    user = get_user_by_id(session['user_id'])
    if not user or user['is_admin']:
        return redirect(url_for('views.admin'))
    if user['role'] == 'client':
        return redirect(url_for('views.jobs'))
    profile = get_profile(session['user_id'])
    requests = get_user_verification_requests(session['user_id'])
    user_jobs = get_jobs_by_user(session['user_id'])
    context = build_context()
    context.update({'user': user, 'profile': profile, 'requests': requests, 'user_jobs': user_jobs})
    return render_template('dashboard.html', **context)


@views.route('/jobs', methods=['GET', 'POST'])
@login_required
def jobs():
    user = get_user_by_id(session['user_id'])
    if not user or user['is_admin']:
        return redirect(url_for('views.admin'))
    if request.method == 'POST':
        if user['is_banned']:
            flash('Your account is banned.', 'warning')
            return redirect(url_for('views.dashboard'))
        if user['role'] == 'client':
            interest = request.form.get('looking_for', '').strip()
            if interest:
                save_client_interest(session['user_id'], interest)
                flash('Your preferences were saved.', 'success')
            else:
                flash('Please tell us what you are looking for.', 'warning')
            return redirect(url_for('views.jobs'))
        if user['role'] != 'freelancer':
            flash('Only freelancers can post services.', 'warning')
            return redirect(url_for('views.jobs'))
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        budget = request.form.get('budget', '').strip()
        if title and description and category:
            job_id = create_job(session['user_id'], title, description, category, budget, '')
            flash('Your service was posted successfully.', 'success')
            return redirect(url_for('views.job_detail', job_id=job_id))
        flash('Please complete the service title, description, and category.', 'warning')
        return redirect(url_for('views.jobs'))

    job_list = get_all_jobs()
    context = build_context()
    context.update({'jobs': job_list})
    return render_template('jobs.html', **context)


@views.route('/jobs/<int:job_id>', methods=['GET', 'POST'])
@login_required
def job_detail(job_id):
    increment_job_view(job_id)
    job = get_job_by_id(job_id)
    if not job:
        abort(404)
    if request.method == 'POST':
        body = request.form.get('message', '').strip()
        if body:
            create_message(job_id, session['user_id'], job['user_id'], body)
            flash('Message sent.', 'success')
        else:
            flash('Please write a message before sending.', 'warning')
        return redirect(url_for('views.job_detail', job_id=job_id))
    messages = get_messages_for_job(job_id)
    context = build_context()
    context.update({'job': job, 'messages': messages})
    return render_template('job_detail.html', **context)


@views.route('/account/delete', methods=['POST'])
@login_required
def request_account_deletion():
    user = get_user_by_id(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    send_account_deletion_email(user['email'], user['full_name'] or user['username'])
    flash('A deletion request email has been prepared for your account.', 'success')
    return redirect(url_for('views.profile'))


@views.route('/profile')
@login_required
def profile():
    user = get_user_by_id(session['user_id'])
    profile = get_profile(session['user_id'])
    context = build_context()
    context.update({'user': user, 'profile': profile})
    return render_template('profile.html', **context)


@views.route('/profile/<int:user_id>')
def public_profile(user_id):
    user = get_user_by_id(user_id)
    if not user:
        abort(404)
    profile = get_profile(user_id)
    context = build_context()
    context.update({'user': user, 'profile': profile, 'public_view': True})
    return render_template('profile.html', **context)


@views.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name', '').strip(),
            'headline_ar': request.form.get('headline_ar', '').strip(),
            'headline_en': request.form.get('headline_en', '').strip(),
            'bio_ar': request.form.get('bio_ar', '').strip(),
            'bio_en': request.form.get('bio_en', '').strip(),
            'skills_ar': request.form.get('skills_ar', '').strip(),
            'skills_en': request.form.get('skills_en', '').strip(),
            'city': request.form.get('city', '').strip(),
            'country': request.form.get('country', '').strip(),
            'hourly_rate': request.form.get('hourly_rate', '').strip(),
            'website': request.form.get('website', '').strip(),
            'availability': request.form.get('availability', '').strip(),
            'phone': request.form.get('phone', '').strip(),
        }
        save_profile(session['user_id'], data)
        flash('Your profile was updated successfully.', 'success')
        return redirect(url_for('views.profile'))

    user = get_user_by_id(session['user_id'])
    profile = get_profile(session['user_id'])
    context = build_context()
    context.update({'user': user, 'profile': profile})
    return render_template('edit_profile.html', **context)


@views.route('/verify', methods=['GET', 'POST'])
@login_required
def verify():
    if request.method == 'POST':
        document_type = request.form.get('document_type', '').strip()
        notes = request.form.get('notes', '').strip()
        if not document_type:
            flash('Please select a document type.', 'warning')
            return redirect(url_for('views.verify'))
        documents = request.files.getlist('document')
        request_id = None
        if documents:
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'verifications')
            os.makedirs(upload_dir, exist_ok=True)
            from .models import create_verification_request
            request_id = create_verification_request(session['user_id'], document_type, notes)
            for document in documents:
                if document and document.filename:
                    filename = secure_filename(document.filename)
                    saved_name = f"{session['user_id']}_{request_id}_{filename}"
                    document.save(os.path.join(upload_dir, saved_name))
                    path = f"/static/uploads/verifications/{saved_name}"
                    create_verification_file(request_id, path)
        if request_id is None:
            from .models import create_verification_request
            request_id = create_verification_request(session['user_id'], document_type, notes)
        flash('Your verification request was sent to the admin team.', 'success')
        return redirect(url_for('views.dashboard'))

    return render_template('verify.html', **build_context())


@views.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy.html', **build_context())


@views.route('/terms')
def terms():
    return render_template('terms.html', **build_context())


@views.route('/admin')
@login_required
def admin():
    user = get_user_by_id(session['user_id'])
    if not user or not user['is_admin']:
        flash('Access denied. Admin privileges are required.', 'warning')
        return redirect(url_for('views.home'))
    users = get_all_users()
    jobs = get_all_jobs()
    verification_requests = [req for req in get_all_verification_requests() if req['status'] == 'pending']
    verification_files = {}
    for req in verification_requests:
        verification_files[req['id']] = get_verification_files(req['id'])
    site_cards = get_all_site_cards()
    context = build_context()
    context.update({'user': user, 'users': users, 'jobs': jobs, 'verification_requests': verification_requests, 'verification_files': verification_files, 'site_cards': site_cards})
    return render_template('admin.html', **context)


@views.route('/admin/verification/<int:request_id>/<status>', methods=['POST'])
@login_required
def review_verification(request_id, status):
    user = get_user_by_id(session['user_id'])
    if not user or not user['is_admin']:
        flash('Access denied. Admin privileges are required.', 'warning')
        return redirect(url_for('views.home'))
    admin_notes = request.form.get('admin_notes', '').strip()
    review_verification_request(request_id, status, admin_notes, session['user_id'])
    if status == 'approved':
        update_user_verification(request_id)
    flash('Verification request updated.', 'success')
    return redirect(url_for('views.admin'))


@views.route('/admin/user/<int:user_id>/<action>', methods=['POST'])
@login_required
def admin_user_action(user_id, action):
    user = get_user_by_id(session['user_id'])
    if not user or not user['is_admin']:
        flash('Access denied. Admin privileges are required.', 'warning')
        return redirect(url_for('views.home'))
    if action == 'ban':
        update_user_status(user_id, True)
        flash('User banned.', 'success')
    elif action == 'unban':
        update_user_status(user_id, False)
        flash('User unbanned.', 'success')
    elif action == 'delete':
        delete_user_account(user_id)
        flash('User deleted.', 'success')
    return redirect(url_for('views.admin'))


@views.route('/admin/job/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job_admin(job_id):
    user = get_user_by_id(session['user_id'])
    if not user or not user['is_admin']:
        flash('Access denied. Admin privileges are required.', 'warning')
        return redirect(url_for('views.home'))
    delete_job(job_id)
    flash('Job deleted.', 'success')
    return redirect(url_for('views.admin'))


@views.route('/admin/card', methods=['POST'])
@login_required
def create_admin_card():
    user = get_user_by_id(session['user_id'])
    if not user or not user['is_admin']:
        flash('Access denied. Admin privileges are required.', 'warning')
        return redirect(url_for('views.home'))
    create_site_card(
        request.form.get('section', 'services'),
        request.form.get('title_ar', '').strip(),
        request.form.get('title_en', '').strip(),
        request.form.get('body_ar', '').strip(),
        request.form.get('body_en', '').strip(),
        request.form.get('icon', '').strip(),
    )
    flash('New marketplace card added.', 'success')
    return redirect(url_for('views.admin'))