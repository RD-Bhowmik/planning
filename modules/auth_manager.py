import sqlite3
import bcrypt
from flask_login import UserMixin
from datetime import datetime

DATABASE_PATH = 'data/users.db'

class User(UserMixin):
    """User model for Flask-Login"""
    def __init__(self, id, username, email, created_at):
        self.id = id
        self.username = username
        self.email = email
        self.created_at = created_at

def init_db():
    """Initialize the user database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
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

def create_user(username, email, password):
    """Create a new user with hashed password"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, created_at))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return True, user_id
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            return False, "Username already exists"
        elif 'email' in str(e):
            return False, "Email already exists"
        return False, "Registration failed"
    except Exception as e:
        return False, str(e)

def verify_user(username, password):
    """Verify user credentials"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, created_at
            FROM users WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            return False, "Invalid username or password"
        
        user_id, username, email, password_hash, created_at = result
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), password_hash):
            user = User(user_id, username, email, created_at)
            return True, user
        else:
            return False, "Invalid username or password"
            
    except Exception as e:
        return False, str(e)

def get_user_by_id(user_id):
    """Get user by ID for Flask-Login"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, created_at
            FROM users WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return User(result[0], result[1], result[2], result[3])
        return None
        
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def get_user_by_username(username):
    """Get user by username"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, created_at
            FROM users WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return User(result[0], result[1], result[2], result[3])
        return None
        
    except Exception as e:
        print(f"Error getting user: {e}")
        return None


