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
        print("⊘ Skipping connection pool (not using PostgreSQL)")
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
        print(f"⚠ WARNING: Could not create connection pool: {e}")
        print("  Falling back to direct connections (still works, just slower)")
        return None

def get_connection():
    """Get a connection from the pool (or create direct connection)"""
    global _connection_pool
    
    if DB_TYPE != 'postgres':
        raise Exception("get_connection() called but not using PostgreSQL")
    
    # If pool doesn't exist, try to initialize it
    if _connection_pool is None:
        init_connection_pool()
    
    # Try to get connection from pool
    if _connection_pool is not None:
        try:
            return _connection_pool.getconn()
        except Exception as e:
            print(f"⚠ Error getting from pool: {e}, using direct connection")
    
    # Fallback: Create direct connection (slower but works)
    try:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        raise

def return_connection(conn):
    """Return a connection to the pool (or close if no pool)"""
    global _connection_pool
    
    if conn is None:
        return
    
    # If we have a pool, return to it; otherwise just close
    if _connection_pool is not None:
        try:
            _connection_pool.putconn(conn)
            return
        except Exception as e:
            print(f"⚠ Error returning to pool: {e}, closing connection")
    
    # Fallback: just close the connection
    try:
        conn.close()
    except Exception as e:
        print(f"⚠ Error closing connection: {e}")

def close_all_connections():
    """Close all connections in the pool (call on shutdown)"""
    global _connection_pool
    
    if _connection_pool is not None:
        _connection_pool.closeall()
        print("✓ Connection pool closed")
