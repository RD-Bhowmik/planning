import bcrypt
import os
from flask_login import UserMixin
from datetime import datetime
from modules.db_config import DB_TYPE, DATABASE_URL

# Import appropriate database driver
if DB_TYPE == 'postgres':
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3

class User(UserMixin):
    """User model for Flask-Login"""
    def __init__(self, id, username, email, created_at):
        self.id = id
        self.username = username
        self.email = email
        self.created_at = created_at

def get_db_connection():
    """Get database connection based on DB_TYPE"""
    if DB_TYPE == 'postgres':
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        return sqlite3.connect(DATABASE_URL)

def init_db():
    """Initialize the user database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgres':
            # PostgreSQL syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
            ''')
            
            # Create indexes for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        else:
            # SQLite syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
        
        conn.commit()
        conn.close()
        
        # Only chmod on local SQLite
        if DB_TYPE == 'sqlite' and not os.environ.get('VERCEL') and os.path.exists(DATABASE_URL):
            try:
                os.chmod(DATABASE_URL, 0o666)
            except:
                pass
                
        print(f"✓ Database initialized successfully ({DB_TYPE})")
    except Exception as e:
        print(f"✗ ERROR initializing database: {e}")
        raise

def create_user(username, email, password):
    """Create a new user with hashed password"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        created_at = datetime.now()
        
        if DB_TYPE == 'postgres':
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', (username, email, password_hash.decode('utf-8'), created_at))
            user_id = cursor.fetchone()[0]
        else:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, created_at.isoformat()))
            user_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return True, user_id
    except Exception as e:
        error_msg = str(e).lower()
        if 'username' in error_msg or 'unique' in error_msg and 'username' in error_msg:
            return False, "Username already exists"
        elif 'email' in error_msg:
            return False, "Email already exists"
        return False, "Registration failed"

def verify_user(username, password):
    """Verify user credentials"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgres':
            cursor.execute('''
                SELECT id, username, email, password_hash, created_at
                FROM users WHERE username = %s
            ''', (username,))
        else:
            cursor.execute('''
                SELECT id, username, email, password_hash, created_at
                FROM users WHERE username = ?
            ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            return False, "Invalid username or password"
        
        user_id, username, email, password_hash, created_at = result
        
        # Handle password hash encoding
        if isinstance(password_hash, str):
            password_hash = password_hash.encode('utf-8')
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), password_hash):
            # Format created_at
            if isinstance(created_at, str):
                created_at_str = created_at
            else:
                created_at_str = created_at.isoformat()
            
            user = User(user_id, username, email, created_at_str)
            return True, user
        else:
            return False, "Invalid username or password"
            
    except Exception as e:
        print(f"Error verifying user: {e}")
        return False, str(e)

def get_user_by_id(user_id):
    """Get user by ID for Flask-Login"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgres':
            cursor.execute('''
                SELECT id, username, email, created_at
                FROM users WHERE id = %s
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT id, username, email, created_at
                FROM users WHERE id = ?
            ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Format created_at
            created_at = result[3]
            if isinstance(created_at, str):
                created_at_str = created_at
            else:
                created_at_str = created_at.isoformat()
            
            return User(result[0], result[1], result[2], created_at_str)
        return None
        
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def get_user_by_username(username):
    """Get user by username"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgres':
            cursor.execute('''
                SELECT id, username, email, created_at
                FROM users WHERE username = %s
            ''', (username,))
        else:
            cursor.execute('''
                SELECT id, username, email, created_at
                FROM users WHERE username = ?
            ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Format created_at
            created_at = result[3]
            if isinstance(created_at, str):
                created_at_str = created_at
            else:
                created_at_str = created_at.isoformat()
            
            return User(result[0], result[1], result[2], created_at_str)
        return None
        
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
