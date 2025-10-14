"""
Database connection pooling for better performance
"""
import os
from modules.db_config import DB_TYPE, DATABASE_URL

# Connection pool (singleton)
_connection_pool = None

if DB_TYPE == 'postgres':
    from psycopg2 import pool
    
    def get_connection_pool():
        """Get or create connection pool"""
        global _connection_pool
        
        if _connection_pool is None:
            try:
                _connection_pool = pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=5,  # Max 5 connections
                    dsn=DATABASE_URL
                )
                print("✓ Connection pool created")
            except Exception as e:
                print(f"✗ Error creating connection pool: {e}")
                raise
        
        return _connection_pool
    
    def get_pooled_connection():
        """Get a connection from the pool"""
        pool = get_connection_pool()
        return pool.getconn()
    
    def return_connection(conn):
        """Return connection to pool"""
        if _connection_pool:
            _connection_pool.putconn(conn)
    
    def close_all_connections():
        """Close all connections in pool"""
        global _connection_pool
        if _connection_pool:
            _connection_pool.closeall()
            _connection_pool = None
else:
    # SQLite doesn't need pooling
    import sqlite3
    
    def get_pooled_connection():
        """Get SQLite connection"""
        return sqlite3.connect(DATABASE_URL)
    
    def return_connection(conn):
        """Close SQLite connection"""
        if conn:
            conn.close()
    
    def close_all_connections():
        """No-op for SQLite"""
        pass

