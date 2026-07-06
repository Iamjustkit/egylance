import os
import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'egylance.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def add_column_if_missing(conn, table_name, column_name, column_def):
    columns = [row[1] for row in conn.execute(f'PRAGMA table_info({table_name})')]
    if column_name not in columns:
        conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_def}')


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'freelancer',
                full_name TEXT,
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_verified INTEGER NOT NULL DEFAULT 0,
                language TEXT NOT NULL DEFAULT 'ar',
                looking_for TEXT,
                visit_count INTEGER NOT NULL DEFAULT 0,
                is_banned INTEGER NOT NULL DEFAULT 0,
                google_id TEXT,
                email_verified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                headline_ar TEXT,
                headline_en TEXT,
                bio_ar TEXT,
                bio_en TEXT,
                skills_ar TEXT,
                skills_en TEXT,
                city TEXT,
                country TEXT,
                hourly_rate TEXT,
                website TEXT,
                availability TEXT,
                phone TEXT,
                is_featured INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS verification_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                document_type TEXT NOT NULL,
                notes TEXT,
                document_path TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                admin_notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS site_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section TEXT NOT NULL,
                title_ar TEXT NOT NULL,
                title_en TEXT NOT NULL,
                body_ar TEXT NOT NULL,
                body_en TEXT NOT NULL,
                icon TEXT
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                budget TEXT,
                location TEXT,
                views_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS verification_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verification_request_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(verification_request_id) REFERENCES verification_requests(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(recipient_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        add_column_if_missing(conn, 'users', 'looking_for', 'looking_for TEXT')
        add_column_if_missing(conn, 'users', 'visit_count', 'visit_count INTEGER NOT NULL DEFAULT 0')
        add_column_if_missing(conn, 'users', 'is_banned', 'is_banned INTEGER NOT NULL DEFAULT 0')
        add_column_if_missing(conn, 'users', 'google_id', 'google_id TEXT')
        add_column_if_missing(conn, 'users', 'email_verified', 'email_verified INTEGER NOT NULL DEFAULT 0')
        add_column_if_missing(conn, 'profiles', 'phone', 'phone TEXT')
        add_column_if_missing(conn, 'jobs', 'views_count', 'views_count INTEGER NOT NULL DEFAULT 0')
        add_column_if_missing(conn, 'verification_requests', 'document_path', 'document_path TEXT')

        if conn.execute('SELECT COUNT(*) FROM site_cards').fetchone()[0] == 0:
            conn.executemany(
                'INSERT INTO site_cards (section, title_ar, title_en, body_ar, body_en, icon) VALUES (?, ?, ?, ?, ?, ?)',
                [
                    ('services', 'برمجة وتطوير', 'Development & Tech', 'مواقع، تطبيقات، وأتمتة أعمال احترافية.', 'Websites, apps, and smart automation for modern teams.', '💻'),
                    ('services', 'تصميم وتواصل بصري', 'Design & Branding', 'هوية بصرية ومحتوى احترافي يرفع مستوى علامتك.', 'Professional branding and visual content that stands out.', '🎨'),
                    ('services', 'كتابة وتسويق', 'Writing & Marketing', 'محتوى عالي الجودة وحملات تسويقية ذكية.', 'High-converting copy and growth-focused campaigns.', '✍️'),
                    ('why', 'التحقق والموثوقية', 'Verification & Trust', 'كل مستقل لديه ملف شخصي موثق ومراجعات حقيقية.', 'Every freelancer has a verified profile and genuine reviews.', '✅'),
                    ('why', 'دفع آمن', 'Secure Payments', 'نظام دفع يحمي كلا الطرفين ويحافظ على الشفافية.', 'Secure payment flows that protect both buyers and sellers.', '🔒'),
                    ('why', 'دعم عربي', 'Arabic Support', 'دعم فني ومحادثات مباشرة بالعربية والإنجليزية.', 'Responsive support in Arabic and English for a better experience.', '💬'),
                ],
            )


def ensure_default_admin():
    with get_db() as conn:
        admin = conn.execute('SELECT id FROM users WHERE is_admin = 1 LIMIT 1').fetchone()
        if not admin:
            create_user('admin', 'admin@egylance.com', 'Admin123!', 'admin', 'Admin User', is_admin=1)


def create_user(username, email, password, role='freelancer', full_name='', is_admin=0, google_id=None, email_verified=0):
    password_hash = generate_password_hash(password)
    try:
        with get_db() as conn:
            cursor = conn.execute(
                'INSERT INTO users (username, email, password_hash, role, full_name, is_admin, language, google_id, email_verified) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (username, email, password_hash, role, full_name, int(is_admin), 'ar', google_id, int(email_verified)),
            )
            user_id = cursor.lastrowid
            conn.execute(
                'INSERT INTO profiles (user_id, headline_ar, headline_en, bio_ar, bio_en) VALUES (?, ?, ?, ?, ?)',
                (user_id, 'مستقل جديد', 'New freelancer', 'أضف وصفك الآن.', 'Add your description now.'),
            )
            return user_id
    except sqlite3.IntegrityError:
        return None


def authenticate_user(identifier, password):
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (identifier, identifier)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None


def get_user_by_id(user_id):
    with get_db() as conn:
        return conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()


def get_all_users():
    with get_db() as conn:
        return conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()


def update_user_status(user_id, is_banned):
    with get_db() as conn:
        conn.execute('UPDATE users SET is_banned = ? WHERE id = ?', (1 if is_banned else 0, user_id))


def delete_user_account(user_id):
    with get_db() as conn:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))


def get_profile(user_id):
    with get_db() as conn:
        return conn.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,)).fetchone()


def save_profile(user_id, data):
    profile = get_profile(user_id)
    with get_db() as conn:
        if profile:
            conn.execute(
                '''
                UPDATE profiles
                SET headline_ar = ?, headline_en = ?, bio_ar = ?, bio_en = ?, skills_ar = ?, skills_en = ?, city = ?, country = ?, hourly_rate = ?, website = ?, availability = ?, phone = ?
                WHERE user_id = ?
                ''',
                (
                    data.get('headline_ar', ''),
                    data.get('headline_en', ''),
                    data.get('bio_ar', ''),
                    data.get('bio_en', ''),
                    data.get('skills_ar', ''),
                    data.get('skills_en', ''),
                    data.get('city', ''),
                    data.get('country', ''),
                    data.get('hourly_rate', ''),
                    data.get('website', ''),
                    data.get('availability', ''),
                    data.get('phone', ''),
                    user_id,
                ),
            )
        else:
            conn.execute(
                '''
                INSERT INTO profiles (user_id, headline_ar, headline_en, bio_ar, bio_en, skills_ar, skills_en, city, country, hourly_rate, website, availability, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    user_id,
                    data.get('headline_ar', ''),
                    data.get('headline_en', ''),
                    data.get('bio_ar', ''),
                    data.get('bio_en', ''),
                    data.get('skills_ar', ''),
                    data.get('skills_en', ''),
                    data.get('city', ''),
                    data.get('country', ''),
                    data.get('hourly_rate', ''),
                    data.get('website', ''),
                    data.get('availability', ''),
                    data.get('phone', ''),
                ),
            )
        conn.execute('UPDATE users SET full_name = ? WHERE id = ?', (data.get('full_name', ''), user_id))


def get_user_language(user_id):
    with get_db() as conn:
        user = conn.execute('SELECT language FROM users WHERE id = ?', (user_id,)).fetchone()
        return user['language'] if user else 'ar'


def save_user_language(user_id, language):
    with get_db() as conn:
        conn.execute('UPDATE users SET language = ? WHERE id = ?', (language, user_id))


def save_client_interest(user_id, interest):
    with get_db() as conn:
        conn.execute('UPDATE users SET looking_for = ? WHERE id = ?', (interest, user_id))


def increment_user_visit(user_id):
    with get_db() as conn:
        conn.execute('UPDATE users SET visit_count = COALESCE(visit_count, 0) + 1 WHERE id = ?', (user_id,))
        visit_count = conn.execute('SELECT visit_count FROM users WHERE id = ?', (user_id,)).fetchone()
        return visit_count['visit_count'] if visit_count else 0


def create_verification_request(user_id, document_type, notes, document_path=None):
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO verification_requests (user_id, document_type, notes, document_path) VALUES (?, ?, ?, ?)',
            (user_id, document_type, notes, document_path),
        )
        return cursor.lastrowid


def create_verification_file(verification_request_id, file_path):
    with get_db() as conn:
        conn.execute(
            'INSERT INTO verification_files (verification_request_id, file_path) VALUES (?, ?)',
            (verification_request_id, file_path),
        )


def get_verification_files(verification_request_id):
    with get_db() as conn:
        return conn.execute(
            'SELECT * FROM verification_files WHERE verification_request_id = ? ORDER BY created_at ASC',
            (verification_request_id,),
        ).fetchall()


def get_verification_files_for_requests(request_ids):
    if not request_ids:
        return []
    placeholders = ','.join('?' for _ in request_ids)
    with get_db() as conn:
        return conn.execute(
            f'SELECT * FROM verification_files WHERE verification_request_id IN ({placeholders}) ORDER BY created_at ASC',
            request_ids,
        ).fetchall()


def get_user_verification_requests(user_id):
    with get_db() as conn:
        return conn.execute('SELECT * FROM verification_requests WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()


def get_all_verification_requests():
    with get_db() as conn:
        return conn.execute(
            'SELECT vr.*, u.username, u.full_name FROM verification_requests vr JOIN users u ON vr.user_id = u.id ORDER BY vr.created_at DESC'
        ).fetchall()


def review_verification_request(request_id, status, admin_notes, reviewer_id):
    with get_db() as conn:
        conn.execute(
            'UPDATE verification_requests SET status = ?, admin_notes = ?, reviewed_at = ? WHERE id = ?',
            (status, admin_notes, datetime.utcnow().isoformat(), request_id),
        )
        if status == 'approved':
            files = conn.execute('SELECT file_path FROM verification_files WHERE verification_request_id = ?', (request_id,)).fetchall()
            for file_row in files:
                file_path = os.path.join(os.path.dirname(__file__), '..', file_row['file_path'].lstrip('/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
            conn.execute('DELETE FROM verification_files WHERE verification_request_id = ?', (request_id,))
        conn.execute(
            'UPDATE users SET is_verified = ? WHERE id = (SELECT user_id FROM verification_requests WHERE id = ?)',
            (1 if status == 'approved' else 0, request_id),
        )


def update_user_verification(request_id):
    with get_db() as conn:
        conn.execute('UPDATE users SET is_verified = 1 WHERE id = (SELECT user_id FROM verification_requests WHERE id = ?)', (request_id,))


def create_job(user_id, title, description, category, budget='', location=''):
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO jobs (user_id, title, description, category, budget, location) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, title, description, category, budget, location),
        )
        return cursor.lastrowid


def get_job_by_id(job_id):
    with get_db() as conn:
        return conn.execute(
            'SELECT j.*, u.username, u.full_name, u.is_verified FROM jobs j JOIN users u ON u.id = j.user_id WHERE j.id = ?',
            (job_id,),
        ).fetchone()


def increment_job_view(job_id):
    with get_db() as conn:
        conn.execute('UPDATE jobs SET views_count = COALESCE(views_count, 0) + 1 WHERE id = ?', (job_id,))


def get_all_jobs(limit=None, query=''):
    with get_db() as conn:
        sql = 'SELECT j.*, u.username, u.full_name FROM jobs j JOIN users u ON u.id = j.user_id'
        params = []
        if query:
            sql += ' WHERE j.title LIKE ? OR j.description LIKE ? OR j.category LIKE ?'
            pattern = f'%{query}%'
            params.extend([pattern, pattern, pattern])
        sql += ' ORDER BY j.created_at DESC'
        if limit:
            sql += ' LIMIT ?'
            params.append(limit)
        return conn.execute(sql, params).fetchall()


def get_jobs_by_user(user_id):
    with get_db() as conn:
        return conn.execute('SELECT j.*, u.username, u.full_name FROM jobs j JOIN users u ON u.id = j.user_id WHERE j.user_id = ? ORDER BY j.created_at DESC', (user_id,)).fetchall()


def delete_job(job_id):
    with get_db() as conn:
        conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))


def create_message(job_id, sender_id, recipient_id, body):
    with get_db() as conn:
        conn.execute(
            'INSERT INTO messages (job_id, sender_id, recipient_id, body) VALUES (?, ?, ?, ?)',
            (job_id, sender_id, recipient_id, body),
        )


def get_messages_for_job(job_id):
    with get_db() as conn:
        return conn.execute(
            'SELECT m.*, u.username, u.full_name FROM messages m JOIN users u ON u.id = m.sender_id WHERE m.job_id = ? ORDER BY m.created_at ASC',
            (job_id,),
        ).fetchall()


def get_site_cards(section):
    with get_db() as conn:
        return conn.execute('SELECT * FROM site_cards WHERE section = ? ORDER BY id', (section,)).fetchall()


def create_site_card(section, title_ar, title_en, body_ar, body_en, icon='✦'):
    with get_db() as conn:
        conn.execute(
            'INSERT INTO site_cards (section, title_ar, title_en, body_ar, body_en, icon) VALUES (?, ?, ?, ?, ?, ?)',
            (section, title_ar, title_en, body_ar, body_en, icon),
        )


def get_all_site_cards():
    with get_db() as conn:
        return conn.execute('SELECT * FROM site_cards ORDER BY section, id').fetchall()


def get_featured_profiles():
    with get_db() as conn:
        return conn.execute(
            '''
            SELECT u.*, p.*
            FROM users u
            JOIN profiles p ON p.user_id = u.id
            WHERE p.is_featured = 1
            ORDER BY u.created_at DESC
            LIMIT 6
            '''
        ).fetchall()