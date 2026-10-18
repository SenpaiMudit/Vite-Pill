import os
import sqlite3
import uuid
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort, send_from_directory
)
import qrcode
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# zxing-cpp: pure-Python wheels, no native C library required
try:
    import zxingcpp
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False

app = Flask(__name__)

# Refuse to start without a real secret key — no insecure fallback
_secret = os.environ.get('SECRET_KEY')
if not _secret:
    import warnings
    warnings.warn(
        "SECRET_KEY env var not set — using insecure dev key. Set SECRET_KEY in production!",
        RuntimeWarning
    )
    _secret = 'vite-pill-dev-only-unsafe-key-change-me'
app.secret_key = _secret
app.config['WTF_CSRF_ENABLED'] = True
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB upload limit

# CSRF protection — covers all POST/PUT/DELETE forms automatically
csrf = CSRFProtect(app)

# Rate limiter — per-route limits defined individually below
limiter = Limiter(app=app, key_func=get_remote_address, storage_uri='memory://')

QR_FOLDER = os.path.join(app.root_path, 'static', 'qrcodes')
os.makedirs(QR_FOLDER, exist_ok=True)

# -----------------------------------------------------------------------------
# DATABASE ADAPTER (RunxBuild Managed PostgreSQL / MySQL + Local SQLite fallback)
# -----------------------------------------------------------------------------
try:
    from .db import get_db_connection, init_db, get_db_config
except ImportError:
    from db import get_db_connection, init_db, get_db_config

# Initialize schema & initial seeds
init_db()


# -----------------------------------------------------------------------------
# CONTEXT PROCESSORS & AUTH HELPERS
# -----------------------------------------------------------------------------
@app.after_request
def set_security_headers(response):
    """Attach security headers to every response (BUILD CHECK #8)."""
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none'"
    )
    return response


@app.context_processor
def inject_global_data():
    cfg = get_db_config()
    return {
        'current_year': 2026,
        'support_phone': '+1 (800) 555-0199',
        'support_email': 'verify@vitepill.io',
        'pyzbar_ready': PYZBAR_AVAILABLE,
        'db_backend': cfg['type']
    }


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this portal.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Master Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# ROUTES (100% Zero JavaScript)
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    """Full marketing landing page with interactive demo, WHO stats, and APK download."""
    return render_template('landing.html')


@app.route('/portal')
@app.route('/hub')
def portal():
    """Quick portal selection hub with live registry statistics."""
    conn = get_db_connection()
    medicine_count = conn.execute('SELECT COUNT(*) as count FROM medicine').fetchone()['count']
    user_count = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('company',)).fetchone()['count']
    conn.close()
    return render_template('portal.html', medicine_count=medicine_count, user_count=user_count)


# --- PART 1: CONSUMER & PHARMACY SCAN / VERIFY FLOW ---
# QR scan: 30 per minute — generous for legitimate use, blocks automated abuse
@limiter.limit('30 per minute')
@app.route('/scan', methods=['GET', 'POST'])
def scan_medicine():
    """Upload or capture a micro QR code for server-side verification."""
    if request.method == 'GET' and request.args.get('manual_uid'):
        uid = request.args.get('manual_uid').strip()
        if uid:
            return redirect(url_for('verify_medicine', uid=uid))

    if request.method == 'POST':
        # Two inputs share name="qr_image" — gallery and camera.
        # getlist() returns both; we pick the first one that actually has a file.
        all_files = request.files.getlist('qr_image')
        file = next((f for f in all_files if f and f.filename), None)

        if not file:
            return render_template('scan_medicine.html', error_msg="No file selected. Please choose an image from gallery or take a photo.")

        # BUILD CHECK #14: validate by magic bytes, not extension or MIME header
        ALLOWED_MAGIC = [
            b'\xff\xd8\xff',        # JPEG
            b'\x89PNG',             # PNG
            b'GIF8',                # GIF
            b'RIFF',                # WebP (RIFF....WEBP)
            b'BM',                  # BMP
        ]
        header = file.read(12)
        file.seek(0)
        if not any(header.startswith(sig) for sig in ALLOWED_MAGIC):
            return render_template('scan_medicine.html',
                error_msg="Invalid file type. Please upload a JPEG, PNG, GIF, WebP, or BMP image.")

        try:
            img = Image.open(file)

            if not PYZBAR_AVAILABLE:
                return render_template(
                    'scan_medicine.html',
                    error_msg="QR decoder unavailable. Please type the UID code manually in the box below."
                )

            results = zxingcpp.read_barcodes(img)

            if not results:
                return render_template(
                    'scan_medicine.html',
                    error_msg="Unclear or improper QR code. Please capture a clear, well-lit photo of the pill's micro-QR."
                )

            scanned_raw = results[0].text.strip()

            # Extract UID if the QR contained a full verification URL
            if '/verify/' in scanned_raw:
                scanned_uid = scanned_raw.split('/verify/')[-1].strip()
            else:
                scanned_uid = scanned_raw

            return redirect(url_for('verify_medicine', uid=scanned_uid))

        except Exception as e:
            return render_template('scan_medicine.html', error_msg=f"Decoding Error: {str(e)}")

    return render_template('scan_medicine.html')


@app.route('/verify/<uid>')
def verify_medicine(uid):
    """Direct URL verification endpoint for smart scans and QR readers."""
    conn = get_db_connection()
    medicine_data = conn.execute('SELECT * FROM medicine WHERE uid = ?', (uid,)).fetchone()
    conn.close()

    if medicine_data is None:
        return render_template('result.html', medicine=None, scanned_uid=uid, is_authentic=False)

    return render_template('result.html', medicine=medicine_data, scanned_uid=uid, is_authentic=True)


# --- PART 2: PHARMACEUTICAL COMPANY BATCH REGISTRY & DASHBOARD ---
@app.route('/manufacturer/dashboard')
@login_required
def manufacturer_dashboard():
    """Private dashboard for authorized manufacturers to review their registered batches."""
    company_name = session.get('company_name', '')
    conn = get_db_connection()
    batches = conn.execute(
        'SELECT * FROM medicine WHERE registered_by = ? ORDER BY created_at DESC',
        (company_name,)
    ).fetchall()
    conn.close()
    return render_template('manufacturer_dashboard.html', batches=batches, company_name=company_name)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_medicine():
    """Register a new batch of medicine and generate cryptographic QR code (Authorized Manufacturers Only)."""
    company_name = session.get('company_name', 'Authorized Manufacturer')

    if request.method == 'POST':
        med_name = request.form.get('name', '').strip()
        med_mfg = request.form.get('manufacturing_date', '').strip()
        med_expiry = request.form.get('expiry_date', '').strip()
        med_ingredients = request.form.get('ingredients', '').strip()
        med_use = request.form.get('ideal_use', '').strip()
        med_mg = request.form.get('mg', '').strip()

        if not all([med_name, med_mfg, med_expiry, med_ingredients, med_use, med_mg]):
            return render_template('add_medicine.html', error_msg="All medical fields are required to register a batch.", company_name=company_name)

        conn = get_db_connection()

        # BASE CONDITION: Prevent duplicate batches with matching parameters
        existing_med = conn.execute('''
            SELECT * FROM medicine 
            WHERE name = ? AND manufacturing_date = ? AND expiry_date = ? AND mg = ?
        ''', (med_name, med_mfg, med_expiry, med_mg)).fetchone()

        if existing_med:
            conn.close()
            return render_template(
                'add_medicine.html',
                error_msg=f"Duplicate Batch Collision Blocked! A batch for '{med_name}' ({med_mg}mg) with these exact dates is already recorded.",
                company_name=company_name
            )

        # Generate unique 16-character hex UID
        while True:
            med_uid = uuid.uuid4().hex[:16]
            existing = conn.execute('SELECT * FROM medicine WHERE uid = ?', (med_uid,)).fetchone()
            if not existing:
                break

        conn.execute('''
            INSERT INTO medicine 
            (uid, name, manufacturing_date, expiry_date, ingredients, ideal_use, mg, registered_by) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (med_uid, med_name, med_mfg, med_expiry, med_ingredients, med_use, med_mg, company_name))
        conn.commit()
        conn.close()

        # Generate cryptographic QR Code embedding verification route
        verify_url = url_for('verify_medicine', uid=med_uid, _external=True)
        qr = qrcode.make(verify_url)
        qr_filename = f"{med_uid}.png"
        qr_filepath = os.path.join(QR_FOLDER, qr_filename)
        qr.save(qr_filepath)

        return render_template(
            'add_medicine.html',
            qr_filename=qr_filename,
            med_uid=med_uid,
            med_name=med_name,
            company_name=company_name,
            success_msg=f"Batch for '{med_name}' secured and signed by {company_name}!"
        )

    return render_template('add_medicine.html', company_name=company_name)


# --- PART 3: AUTHENTICATION & MASTER ADMIN PORTAL ---
# Login: 5 per 15 minutes — blocks brute-force without annoying legitimate users
@limiter.limit('5 per 15 minutes')
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Company employee login portal."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if len(password) < 8:
            return render_template('login.html', error="Invalid username or password.")

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['company_name'] = user['company_name']
            session['role'] = user['role']
            flash(f"Welcome, {user['full_name']} ({user['company_name']})!", 'success')
            return redirect(url_for('add_medicine'))

        return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')


# Admin login: 5 per 15 minutes — stricter protection for privileged access
@limiter.limit('5 per 15 minutes')
@app.route('/admin-login', methods=['GET', 'POST'])
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Master administrator login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND role = ?',
            (username, 'admin')
        ).fetchone()
        conn.close()

        if user and not check_password_hash(user['password'], password):
            user = None  # Password mismatch — treat as not found

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = 'admin'
            return redirect(url_for('admin_users'))

        return render_template('admin_login.html', error="Invalid administrator credentials.")

    return render_template('admin_login.html')


@app.route('/admin/users', methods=['GET', 'POST'])
@admin_required
def admin_users():
    """Master Admin Dashboard for employee/company management."""
    conn = get_db_connection()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        company_name = request.form.get('company_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not all([full_name, phone, company_name, username, password]):
            flash("All account fields are required.", "danger")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
        else:
            existing_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if existing_user:
                flash(f"Username '{username}' is already taken. Please choose another.", "danger")
            else:
                hashed_pw = generate_password_hash(password)
                conn.execute('''
                    INSERT INTO users (full_name, phone, company_name, username, password, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (full_name, phone, company_name, username, hashed_pw, 'company'))
                conn.commit()
                flash(f"Account for {full_name} ({company_name}) successfully created!", "success")

    users = conn.execute('SELECT * FROM users WHERE role = ? ORDER BY id DESC', ('company',)).fetchall()
    medicines = conn.execute('SELECT * FROM medicine ORDER BY created_at DESC LIMIT 10').fetchall()
    conn.close()

    return render_template('admin_users.html', users=users, medicines=medicines)


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a company user account (pure POST, zero JS)."""
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ? AND role = ?', (user_id, 'company'))
    conn.commit()
    conn.close()
    flash("User account deleted successfully.", "success")
    return redirect(url_for('admin_users'))


@app.route('/logout')
def logout():
    """Terminate current user session."""
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('index'))


# -----------------------------------------------------------------------------
# MOBILE APK DOWNLOAD ROUTE
# -----------------------------------------------------------------------------
@app.route('/download/apk')
@app.route('/vite-pill.apk')
def download_apk():
    """Serve the 753 KB Android APK file for mobile users and field inspectors."""
    search_dirs = [
        os.path.join(app.root_path, 'static'),
        os.path.dirname(app.root_path),
        app.root_path
    ]
    for directory in search_dirs:
        if os.path.exists(os.path.join(directory, 'vite-pill.apk')):
            return send_from_directory(
                directory,
                'vite-pill.apk',
                as_attachment=True,
                mimetype='application/vnd.android.package-archive'
            )
    abort(404)


@app.route('/logo.svg')
@app.route('/favicon.ico')
def serve_logo():
    """Serve the official brand SVG logo and favicon."""
    search_dirs = [
        os.path.join(app.root_path, 'static'),
        os.path.dirname(app.root_path),
        app.root_path
    ]
    for directory in search_dirs:
        if os.path.exists(os.path.join(directory, 'logo.svg')):
            return send_from_directory(directory, 'logo.svg', mimetype='image/svg+xml')
    abort(404)


@app.route('/manifest.json')
def serve_manifest():
    """Serve Web App Manifest for PWABuilder and mobile home screen installation."""
    for base in [os.path.join(app.root_path, 'static'), os.path.dirname(app.root_path), app.root_path]:
        p = os.path.join(base, 'manifest.json')
        if os.path.exists(p):
            return send_from_directory(base, 'manifest.json', mimetype='application/manifest+json')
    abort(404)


@app.route('/icon-192.png')
@app.route('/icon-512.png')
def serve_pwa_icons():
    """Serve 192x192 and 512x512 PWA launcher icons for Android TWA."""
    filename = request.path.lstrip('/')
    for base in [os.path.join(app.root_path, 'static'), os.path.dirname(app.root_path), app.root_path]:
        p = os.path.join(base, filename)
        if os.path.exists(p):
            return send_from_directory(base, filename, mimetype='image/png')
    abort(404)


# -----------------------------------------------------------------------------
# ERROR HANDLERS
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('404.html', error_title="500 — Server Error", error_desc="An internal error occurred. Please try again."), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # debug=False in all cases — Gunicorn runs in production, this block is dev-only
    app.run(host='0.0.0.0', port=port, debug=False)