import json
import os

def get_user_data_filepath(user_id):
    """Get the filepath for a specific user's data"""
    return f'data/user_{user_id}.json'

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
            "tax_rate_percent": 30.0,
            "default_loan_repayment": 0,
            "loan_interest_rate": 0,
            "loan_period_months": 12,
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

def load_financial_data(user_id=None, is_guest=False, guest_data=None):
    """
    Loads financial data based on user type:
    - Logged-in users: Load from their specific file
    - Guest users: Use session data or create new default data
    """
    if is_guest:
        # For guest users, use provided session data or return default
        if guest_data:
            return guest_data
        return get_default_financial_data()
    
    if user_id is None:
        # Fallback to original file (for backwards compatibility)
        filepath = 'data/financial_plan.json'
    else:
        filepath = get_user_data_filepath(user_id)
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # If user file doesn't exist, create it with default data
        if user_id is not None:
            default_data = get_default_financial_data()
            save_financial_data(default_data, user_id=user_id)
            return default_data
        print(f"Error: The file at {filepath} was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file at {filepath}.")
        return None

def save_financial_data(data, user_id=None, is_guest=False):
    """
    Saves financial data based on user type:
    - Logged-in users: Save to their specific file
    - Guest users: Don't save to disk (only kept in session)
    """
    if is_guest:
        # For guest users, don't save to disk
        # Data will be returned to be stored in session
        return True
    
    if user_id is None:
        # Fallback to original file (for backwards compatibility)
        filepath = 'data/financial_plan.json'
    else:
        filepath = get_user_data_filepath(user_id)
    
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"An error occurred while saving data: {e}")
        return False



