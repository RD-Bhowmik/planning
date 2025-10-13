import json

def load_financial_data(filepath='data/financial_plan.json'):
    """Loads financial data from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file at {filepath} was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file at {filepath}.")
        return None

def save_financial_data(data, filepath='data/financial_plan.json'):
    """Saves financial data to a JSON file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"An error occurred while saving data: {e}")
        return False



