"""
Data Manager - Unified interface for financial data storage
Automatically routes to PostgreSQL or JSON based on configuration
"""
from modules.db_config import DB_TYPE
from modules.financial_db import (
    get_default_financial_data,
    load_financial_data_postgres,
    save_financial_data_postgres,
    load_financial_data_json,
    save_financial_data_json
)

def load_financial_data(user_id=None, is_guest=False, guest_data=None):
    """
    Load financial data - automatically uses correct storage backend
    """
    if DB_TYPE == 'postgres' and not is_guest:
        return load_financial_data_postgres(user_id)
    else:
        return load_financial_data_json(user_id, is_guest, guest_data)

def save_financial_data(data, user_id=None, is_guest=False):
    """
    Save financial data - automatically uses correct storage backend
    """
    if DB_TYPE == 'postgres' and not is_guest:
        return save_financial_data_postgres(user_id, data)
    else:
        return save_financial_data_json(user_id, data, is_guest)

# Re-export for compatibility
__all__ = ['load_financial_data', 'save_financial_data', 'get_default_financial_data']
