"""
Database configuration for both local (SQLite) and production (PostgreSQL)
"""
import os

# Detect environment
IS_VERCEL = os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')
USE_POSTGRES = os.environ.get('POSTGRES_URL') is not None

if USE_POSTGRES:
    # Vercel Postgres connection string
    DATABASE_URL = os.environ.get('POSTGRES_URL')
    DB_TYPE = 'postgres'
    print(f"Using PostgreSQL database")
else:
    # Local SQLite fallback
    DATABASE_URL = 'data/users.db'
    DB_TYPE = 'sqlite'
    print(f"Using SQLite database at {DATABASE_URL}")
    
    # Ensure data directory exists
    if not IS_VERCEL:
        os.makedirs('data', exist_ok=True)

