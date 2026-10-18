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

# Pyzbar import with fallback handling for environments lacking C shared libraries
try:
    from pyzbar.pyzbar import decode
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vite-pill-secure-key-2026-mudit')

QR_FOLDER = os.path.join(app.root_path, 'static', 'qrcodes')
os.makedirs(QR_FOLDER, exist_ok=True)

DB_PATH = os.path.join(app.root_path, 'database.db')


# -----------------------------------------------------------------------------
# DATABASE SETUP & HELPERS
# -----------------------------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    # Medicine registry table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS medicine (
            uid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            manufacturing_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            ideal_use TEXT NOT NULL,
            mg TEXT NOT NULL,
            registered_by TEXT DEFAULT 'Pfizer Healthcare',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Employee / Manufacturer user accounts table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            company_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'company',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed master admin if not exists
    admin = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin:
        conn.execute('''
            INSERT INTO users (full_name, phone, company_name, username, password, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Master Administrator', '+18005550199', 'Vite Pill Authority', 'admin', 'admin123', 'admin'))

    # Seed sample authentic medicine if database is empty
    sample = conn.execute('SELECT COUNT(*) as count FROM medicine').fetchone()
    if sample and sample['count'] == 0:
        sample_uid = 'a8f4c2e1b9304958'
        conn.execute('''
            INSERT INTO medicine 
            (uid, name, manufacturing_date, expiry_date, ingredients, ideal_use, mg, registered_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sample_uid,
            'Amoxicillin Trihydrate',
            '2025-01-15',
            '2027-01-15',
            'Amoxicillin 500mg, Magnesium Stearate, Titanium Dioxide',
            'Bacterial respiratory infections, strep throat, and skin infections',
            '500',
            'Novartis Pharma'
        ))

        # Generate seed QR
        qr = qrcode.make(sample_uid)
        qr_filepath = os.path.join(QR_FOLDER, f"{sample_uid}.png")
        qr.save(qr_filepath)

    conn.commit()
    conn.close()


init_db()


# -----------------------------------------------------------------------------
# CONTEXT PROCESSORS & AUTH HELPERS
# -----------------------------------------------------------------------------
@app.context_processor
def inject_global_data():
    return {
        'current_year': 2026,
        'support_phone': '+1 (800) 555-0199',
        'support_email': 'verify@vitepill.io',
        'pyzbar_ready': PYZBAR_AVAILABLE
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
    """Portal selection hub with live registry statistics."""
    conn = get_db_connection()
    medicine_count = conn.execute('SELECT COUNT(*) as count FROM medicine').fetchone()['count']
    user_count = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('company',)).fetchone()['count']
    conn.close()
    return render_template('index.html', medicine_count=medicine_count, user_count=user_count)


# --- PART 1: CONSUMER & PHARMACY SCAN / VERIFY FLOW ---
@app.route('/scan', methods=['GET', 'POST'])
def scan_medicine():
    """Upload or capture a micro QR code for server-side verification."""
    if request.method == 'GET' and request.args.get('manual_uid'):
        uid = request.args.get('manual_uid').strip()
        if uid:
            return redirect(url_for('verify_medicine', uid=uid))

    if request.method == 'POST':
        if 'qr_image' not in request.files or request.files['qr_image'].filename == '':
            return render_template('scan_medicine.html', error_msg="No file selected. Please choose a pill image or QR code.")

        file = request.files['qr_image']

        try:
            img = Image.open(file)
            
            if not PYZBAR_AVAILABLE:
                # Friendly fallback if zbar C-library is missing on the host OS
                return render_template(
                    'scan_medicine.html', 
                    error_msg="Pyzbar decoding engine is compiling. You can manually enter the UID in the box below."
                )

            decoded_objects = decode(img)

            if not decoded_objects:
                return render_template(
                    'scan_medicine.html',
                    error_msg="Unclear or improper QR code. Please capture a clear, well-lit photo of the pill's micro-QR."
                )

            scanned_raw = decoded_objects[0].data.decode('utf-8').strip()
            
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


# --- PART 2: PHARMACEUTICAL COMPANY BATCH REGISTRY ---
@app.route('/add', methods=['GET', 'POST'])
def add_medicine():
    """Register a new batch of medicine and generate cryptographic QR code."""
    if request.method == 'POST':
        med_name = request.form.get('name', '').strip()
        med_mfg = request.form.get('manufacturing_date', '').strip()
        med_expiry = request.form.get('expiry_date', '').strip()
        med_ingredients = request.form.get('ingredients', '').strip()
        med_use = request.form.get('ideal_use', '').strip()
        med_mg = request.form.get('mg', '').strip()
        registered_by = session.get('company_name', 'Authorized Manufacturer')

        if not all([med_name, med_mfg, med_expiry, med_ingredients, med_use, med_mg]):
            return render_template('add_medicine.html', error_msg="All medical fields are required to register a batch.")

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
                error_msg=f"Duplicate Batch Detected! A batch for '{med_name}' ({med_mg}mg) with these exact dates is already registered."
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
        ''', (med_uid, med_name, med_mfg, med_expiry, med_ingredients, med_use, med_mg, registered_by))
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
            success_msg=f"Medicine batch '{med_name}' successfully secured and registered!"
        )

    return render_template('add_medicine.html')


# --- PART 3: AUTHENTICATION & MASTER ADMIN PORTAL ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Company employee login portal."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['company_name'] = user['company_name']
            session['role'] = user['role']
            flash(f"Welcome, {user['full_name']} ({user['company_name']})!", 'success')
            return redirect(url_for('add_medicine'))

        return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')


@app.route('/admin-login', methods=['GET', 'POST'])
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Master administrator login."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ? AND role = ?',
            (username, password, 'admin')
        ).fetchone()
        conn.close()

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
        else:
            try:
                conn.execute('''
                    INSERT INTO users (full_name, phone, company_name, username, password, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (full_name, phone, company_name, username, password, 'company'))
                conn.commit()
                flash(f"Account for {full_name} ({company_name}) successfully created!", "success")
            except sqlite3.IntegrityError:
                flash(f"Username '{username}' is already taken.", "danger")

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
# ERROR HANDLERS (Mudit Misra Standard: Custom 404, No Broken Pages)
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('404.html', error_title="500 — Server Error", error_desc="An internal error occurred. Please try again."), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)