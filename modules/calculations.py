def calculate_net_income(gross_income, tax_rate_percent):
    """Calculates net income after applying tax."""
    tax_amount = (gross_income * tax_rate_percent) / 100
    return gross_income - tax_amount

def calculate_total_daily_net_income(daily_entries, tax_rate_percent):
    """Calculates the sum of net income from all daily entries."""
    total_net_income = 0
    for entry in daily_entries:
        total_net_income += calculate_net_income(entry['gross_income'], tax_rate_percent)
    return total_net_income

def calculate_remaining_capital(total_capital, expenses):
    """Calculates the remaining capital after deducting expenses."""
    total_expenses = sum(expense['amount'] for expense in expenses)
    return total_capital - total_expenses

def calculate_monthly_savings(monthly_cash_flow):
    """Calculates savings for each month."""
    savings_list = []
    for month_data in monthly_cash_flow:
        savings = month_data['income'] - month_data['loan_repayment']
        savings_list.append({
            'month': month_data['month'],
            'savings': round(savings, 2)
        })
    return savings_list

def calculate_total_savings(monthly_savings):
    """Calculates the total accumulated savings."""
    return sum(item['savings'] for item in monthly_savings)

def calculate_total_expenses_from_savings(expenses):
    """Calculates the total amount of expenses to be deducted from savings."""
    return sum(expense['amount'] for expense in expenses)
