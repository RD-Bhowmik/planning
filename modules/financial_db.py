"""
Financial data storage - supports both PostgreSQL and JSON fallback
WITH CONNECTION POOLING AND CACHING for better performance
"""
import json
import os
from modules.db_config import DB_TYPE, DATABASE_URL
from modules.cache import get_cached, set_cache, invalidate_user_cache

# Import appropriate database driver
if DB_TYPE == 'postgres':
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    from modules.db_pool import get_connection, return_connection

def init_financial_tables():
    """Initialize financial data tables in PostgreSQL"""
    if DB_TYPE != 'postgres':
        return  # Skip for SQLite (uses JSON files)
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        # Create financial_data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_data (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                profile JSONB DEFAULT '{}',
                settings JSONB DEFAULT '{}',
                capital JSONB DEFAULT '{}',
                monthly_cash_flow JSONB DEFAULT '[]',
                expenses_from_savings JSONB DEFAULT '[]',
                daily_income_tracker JSONB DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_financial_user_id ON financial_data(user_id)')
        
        conn.commit()
        conn.close()
        print("✓ Financial tables initialized (PostgreSQL)")
    except Exception as e:
        print(f"✗ ERROR initializing financial tables: {e}")
        raise

def get_default_financial_data():
    """Returns default financial data structure for new users"""
    return {
        "profile": {
            "name": "Your Name",
            "goal": "Financial Planning"
        },
        "settings": {
            "target_currency": "AUD",
            "bdt_to_aud_rate": 0.0127,
            "bdt_to_usd_rate": 0.0091,
            "bdt_to_nzd_rate": 0.0135,
            "tax_rate_percent": 0.0,
            "default_loan_repayment": 0,
            "loan_interest_rate": 0,
            "loan_period_months": 60,
            "table_sort_order": "newest_first"
        },
        "capital": {
            "sources": [
                {"name": "Parents", "amount_bdt": 0},
                {"name": "Friend", "amount_bdt": 0},
                {"name": "Loan", "amount_bdt": 0}
            ],
            "expenses_from_capital": []
        },
        "monthly_cash_flow": [],
        "expenses_from_savings": [],
        "daily_income_tracker": []
    }

def load_financial_data_postgres(user_id):
    """Load financial data from PostgreSQL with caching"""
    # Try cache first
    cache_key = f"financial_data:{user_id}"
    cached_data = get_cached(cache_key)
    if cached_data is not None:
        return cached_data
    
    # If not in cache, load from database
    conn = None
    try:
        conn = get_connection()  # Get from connection pool
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
            SELECT profile, settings, capital, monthly_cash_flow, 
                   expenses_from_savings, daily_income_tracker
            FROM financial_data WHERE user_id = %s
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            data = {
                "profile": result['profile'] or {},
                "settings": result['settings'] or {},
                "capital": result['capital'] or {"sources": [], "expenses_from_capital": []},
                "monthly_cash_flow": result['monthly_cash_flow'] or [],
                "expenses_from_savings": result['expenses_from_savings'] or [],
                "daily_income_tracker": result['daily_income_tracker'] or []
            }
            # Cache the result for 30 seconds
            set_cache(cache_key, data, ttl=30)
            return data
        else:
            # Create default data for new user
            default_data = get_default_financial_data()
            save_financial_data_postgres(user_id, default_data)
            return default_data
            
    except Exception as e:
        print(f"Error loading financial data from PostgreSQL: {e}")
        return None
    finally:
        if conn:
            return_connection(conn)  # Return to pool

def save_financial_data_postgres(user_id, data):
    """Save financial data to PostgreSQL and invalidate cache"""
    conn = None
    try:
        conn = get_connection()  # Get from connection pool
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO financial_data 
            (user_id, profile, settings, capital, monthly_cash_flow, 
             expenses_from_savings, daily_income_tracker, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) 
            DO UPDATE SET
                profile = EXCLUDED.profile,
                settings = EXCLUDED.settings,
                capital = EXCLUDED.capital,
                monthly_cash_flow = EXCLUDED.monthly_cash_flow,
                expenses_from_savings = EXCLUDED.expenses_from_savings,
                daily_income_tracker = EXCLUDED.daily_income_tracker,
                updated_at = CURRENT_TIMESTAMP
        ''', (
            user_id,
            Json(data.get('profile', {})),
            Json(data.get('settings', {})),
            Json(data.get('capital', {})),
            Json(data.get('monthly_cash_flow', [])),
            Json(data.get('expenses_from_savings', [])),
            Json(data.get('daily_income_tracker', []))
        ))
        
        conn.commit()
        
        # Invalidate cache for this user
        invalidate_user_cache(user_id)
        
        return True
        
    except Exception as e:
        print(f"Error saving financial data to PostgreSQL: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            return_connection(conn)  # Return to pool

def load_financial_data_json(user_id=None, is_guest=False, guest_data=None):
    """Load financial data from JSON files (fallback for local/SQLite)"""
    if is_guest:
        if guest_data:
            return guest_data
        return get_default_financial_data()
    
    if user_id is None:
        return None
    
    filepath = f'data/user_{user_id}.json'
    
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading financial data: {e}")
            return None
    else:
        # Create default data file for new user
        default_data = get_default_financial_data()
        save_financial_data_json(user_id, default_data)
        return default_data

def save_financial_data_json(user_id, data, is_guest=False):
    """Save financial data to JSON files (fallback for local/SQLite)"""
    if is_guest:
        return True  # Guest data handled by session
    
    if user_id is None:
        return False
    
    filepath = f'data/user_{user_id}.json'
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving financial data: {e}")
        return False

