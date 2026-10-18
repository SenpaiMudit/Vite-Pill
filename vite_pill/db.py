"""
Vite Pill Database Adapter
Supports:
1. RunxBuild Managed PostgreSQL (via DATABASE_URL or DB_* environment variables)
2. RunxBuild Managed MySQL (via DATABASE_URL or DB_* environment variables)
3. Local SQLite fallback (database.db) for zero-configuration development
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from typing import Any, Dict, List, Optional, Tuple


def get_db_config():
    """Detect database provider from environment variables."""
    raw_url = os.environ.get('DATABASE_URL') or os.environ.get('NETLIFY_DATABASE_URL')
    if raw_url:
        # Standardize postgres:// to postgresql://
        if raw_url.startswith('postgres://'):
            raw_url = 'postgresql://' + raw_url[len('postgres://'):]
        if raw_url.startswith('postgresql'):
            return {'type': 'postgres', 'url': raw_url}
        elif raw_url.startswith('mysql'):
            return {'type': 'mysql', 'url': raw_url}

    # Check discrete cloud environment variables (e.g. RunxBuild, Heroku, Render)
    db_host = os.environ.get('DB_HOST') or os.environ.get('PGHOST') or os.environ.get('MYSQL_HOST')
    if db_host:
        db_port = os.environ.get('DB_PORT') or os.environ.get('PGPORT') or os.environ.get('MYSQL_PORT')
        db_name = os.environ.get('DB_NAME') or os.environ.get('PGDATABASE') or os.environ.get('MYSQL_DATABASE', 'vite_pill')
        db_user = os.environ.get('DB_USER') or os.environ.get('PGUSER') or os.environ.get('MYSQL_USER', 'root')
        db_pass = os.environ.get('DB_PASSWORD') or os.environ.get('PGPASSWORD') or os.environ.get('MYSQL_PASSWORD', '')

        if db_port in ['3306', 3306] or os.environ.get('MYSQL_HOST'):
            return {
                'type': 'mysql',
                'host': db_host,
                'port': int(db_port) if db_port else 3306,
                'user': db_user,
                'password': db_pass,
                'database': db_name
            }
        else:
            return {
                'type': 'postgres',
                'host': db_host,
                'port': int(db_port) if db_port else 5442,
                'user': db_user,
                'password': db_pass,
                'database': db_name
            }

    # Default: Local SQLite
    db_path = os.environ.get('SQLITE_PATH')
    if not db_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'database.db')
    return {'type': 'sqlite', 'path': db_path}


class CursorWrapper:
    """Provides a uniform cursor interface returning dictionary-like rows across all DB drivers."""
    def __init__(self, raw_cursor, db_type: str):
        self._cursor = raw_cursor
        self._db_type = db_type

    def fetchone(self) -> Optional[Dict[str, Any]]:
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._db_type == 'sqlite':
            return dict(row)
        return dict(row)

    def fetchall(self) -> List[Dict[str, Any]]:
        rows = self._cursor.fetchall()
        if not rows:
            return []
        return [dict(r) for r in rows]

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def close(self):
        try:
            self._cursor.close()
        except Exception:
            pass


class DBConnection:
    """Unified Database Connection supporting SQLite, PostgreSQL, and MySQL with parameter normalization."""
    def __init__(self, raw_conn, db_type: str):
        self.raw_conn = raw_conn
        self.db_type = db_type

    def execute(self, query: str, params: Tuple = ()) -> CursorWrapper:
        # Convert SQLite-style '?' placeholders to '%s' for Postgres/MySQL
        if self.db_type in ('postgres', 'mysql'):
            query = query.replace('?', '%s')
            cursor = self.raw_conn.cursor()
            cursor.execute(query, params)
            return CursorWrapper(cursor, self.db_type)
        else:
            cursor = self.raw_conn.execute(query, params)
            return CursorWrapper(cursor, 'sqlite')

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        try:
            self.raw_conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_db_connection() -> DBConnection:
    """Factory creating connected DBConnection instance according to environment configuration."""
    cfg = get_db_config()
    db_type = cfg['type']

    if db_type == 'postgres':
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise RuntimeError(
                "psycopg2 is required for PostgreSQL. Please install 'psycopg2-binary'."
            )
        if 'url' in cfg:
            conn = psycopg2.connect(cfg['url'], cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            conn = psycopg2.connect(
                host=cfg['host'],
                port=cfg['port'],
                user=cfg['user'],
                password=cfg['password'],
                dbname=cfg['database'],
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        return DBConnection(conn, 'postgres')

    elif db_type == 'mysql':
        try:
            import pymysql
            import pymysql.cursors
        except ImportError:
            raise RuntimeError(
                "pymysql is required for MySQL. Please install 'pymysql'."
            )
        if 'url' in cfg:
            # Parse mysql://user:password@host:port/dbname
            import urllib.parse
            url = urllib.parse.urlparse(cfg['url'])
            conn = pymysql.connect(
                host=url.hostname,
                port=url.port or 3306,
                user=url.username,
                password=url.password,
                database=url.path.lstrip('/'),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        else:
            conn = pymysql.connect(
                host=cfg['host'],
                port=cfg['port'],
                user=cfg['user'],
                password=cfg['password'],
                database=cfg['database'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        return DBConnection(conn, 'mysql')

    else:
        # SQLite
        conn = sqlite3.connect(cfg['path'])
        conn.row_factory = sqlite3.Row
        return DBConnection(conn, 'sqlite')


def init_db():
    """Initializes schema and baseline administrator and demo records."""
    cfg = get_db_config()
    db_type = cfg['type']
    conn = get_db_connection()

    try:
        if db_type == 'postgres':
            conn.execute('''
                CREATE TABLE IF NOT EXISTS medicine (
                    uid VARCHAR(64) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    manufacturing_date VARCHAR(64) NOT NULL,
                    expiry_date VARCHAR(64) NOT NULL,
                    ingredients TEXT NOT NULL,
                    ideal_use TEXT NOT NULL,
                    mg VARCHAR(64) NOT NULL,
                    registered_by VARCHAR(255) DEFAULT 'Pfizer Healthcare',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    phone VARCHAR(64) NOT NULL,
                    company_name VARCHAR(255) NOT NULL,
                    username VARCHAR(128) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(64) NOT NULL DEFAULT 'company',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
        elif db_type == 'mysql':
            conn.execute('''
                CREATE TABLE IF NOT EXISTS medicine (
                    uid VARCHAR(64) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    manufacturing_date VARCHAR(64) NOT NULL,
                    expiry_date VARCHAR(64) NOT NULL,
                    ingredients TEXT NOT NULL,
                    ideal_use TEXT NOT NULL,
                    mg VARCHAR(64) NOT NULL,
                    registered_by VARCHAR(255) DEFAULT 'Pfizer Healthcare',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    phone VARCHAR(64) NOT NULL,
                    company_name VARCHAR(255) NOT NULL,
                    username VARCHAR(128) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(64) NOT NULL DEFAULT 'company',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
        else:
            # SQLite
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
                );
            ''')
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
                );
            ''')

        conn.commit()

        # Seed master admin if not exists
        admin = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
        if not admin:
            conn.execute('''
                INSERT INTO users (full_name, phone, company_name, username, password, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('Master Administrator', '+18005550199', 'Vite Pill Authority', 'admin',
                  generate_password_hash('admin123'), 'admin'))
            conn.commit()

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
            conn.commit()

    finally:
        conn.close()
