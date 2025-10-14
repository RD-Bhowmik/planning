"""
Connection pooling for PostgreSQL to dramatically improve performance
"""
from modules.db_config import DB_TYPE, DATABASE_URL

# Only import psycopg2 if using PostgreSQL
if DB_TYPE == 'postgres':
    import psycopg2
    from psycopg2 import pool

# Global connection pool
_connection_pool = None

def init_connection_pool():
    """Initialize the connection pool (call once at startup)"""
    global _connection_pool
    
    if DB_TYPE != 'postgres':
        return None
    
    try:
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,      # Minimum connections to keep open
            maxconn=10,     # Maximum connections in the pool
            dsn=DATABASE_URL,
            sslmode='require'
        )
        print("✓ PostgreSQL connection pool initialized (1-10 connections)")
        return _connection_pool
    except Exception as e:
        print(f"✗ ERROR creating connection pool: {e}")
        return None

def get_connection():
    """Get a connection from the pool"""
    global _connection_pool
    
    if _connection_pool is None:
        init_connection_pool()
    
    try:
        return _connection_pool.getconn()
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
        # Fallback to direct connection
        return psycopg2.connect(DATABASE_URL, sslmode='require')

def return_connection(conn):
    """Return a connection to the pool"""
    global _connection_pool
    
    if _connection_pool is None:
        conn.close()
    else:
        try:
            _connection_pool.putconn(conn)
        except Exception as e:
            print(f"Error returning connection to pool: {e}")
            conn.close()

def close_all_connections():
    """Close all connections in the pool (call on shutdown)"""
    global _connection_pool
    
    if _connection_pool is not None:
        _connection_pool.closeall()
        print("✓ Connection pool closed")
