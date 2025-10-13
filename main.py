
from flask import Flask, render_template, request, redirect, url_for
from collections import defaultdict
from datetime import datetime
from waitress import serve
from modules.data_manager import load_financial_data, save_financial_data
from modules.calculations import (
    calculate_remaining_capital,
    calculate_monthly_savings,
    calculate_total_savings,
    calculate_total_expenses_from_savings,
    calculate_net_income,
    calculate_total_daily_net_income
)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

@app.context_processor
def inject_date_pickers_data():
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 6))
    months = [
        {'value': '01', 'name': 'January'}, {'value': '02', 'name': 'February'},
        {'value': '03', 'name': 'March'}, {'value': '04', 'name': 'April'},
        {'value': '05', 'name': 'May'}, {'value': '06', 'name': 'June'},
        {'value': '07', 'name': 'July'}, {'value': '08', 'name': 'August'},
        {'value': '09', 'name': 'September'}, {'value': '10', 'name': 'October'},
        {'value': '11', 'name': 'November'}, {'value': '12', 'name': 'December'}
    ]
    return dict(years=years, months=months)

def get_all_financial_data():
    financial_data = load_financial_data()
    if not financial_data:
        return None

    profile_data = financial_data.get('profile', {})
    settings_data = financial_data.get('settings', {})
    capital_data = financial_data.get('capital', {})
    monthly_cash_flow = financial_data.get('monthly_cash_flow', [])
    expenses_from_savings = financial_data.get('expenses_from_savings', [])
    daily_income_tracker = financial_data.get('daily_income_tracker', [])
    tax_rate = settings_data.get('tax_rate_percent', 30.0)

    bdt_rate = settings_data.get('bdt_to_aud_rate', 0.0127)

    # Convert BDT sources to AUD and calculate total capital
    total_capital_aud = 0
    for source in capital_data.get('sources', []):
        source['amount_aud'] = source.get('amount_bdt', 0) * bdt_rate
        total_capital_aud += source['amount_aud']
    capital_data['total_capital_aud'] = total_capital_aud

    # Perform calculations with the newly calculated total capital
    remaining_capital = calculate_remaining_capital(total_capital_aud, capital_data.get('expenses_from_capital', []))
    monthly_savings = calculate_monthly_savings(monthly_cash_flow)
    total_savings = calculate_total_savings(monthly_savings)
    total_expenses_from_savings = calculate_total_expenses_from_savings(expenses_from_savings)
    # New logic: Net savings now includes remaining capital
    net_savings = (total_savings - total_expenses_from_savings) + remaining_capital
    total_net_daily_income = calculate_total_daily_net_income(daily_income_tracker, tax_rate)

    # New: Group daily income by month
    daily_income_by_month = defaultdict(lambda: {'entries': [], 'total_net': 0})
    for entry in daily_income_tracker:
        try:
            month_key = datetime.strptime(entry['date'], '%Y-%m-%d').strftime('%Y-%m')
            net_income = calculate_net_income(entry['gross_income'], tax_rate)
            daily_income_by_month[month_key]['entries'].append(entry)
            daily_income_by_month[month_key]['total_net'] += net_income
        except ValueError:
            continue # Skip entries with invalid date format

    # Sort months chronologically
    sorted_months = sorted(daily_income_by_month.items(), key=lambda item: item[0], reverse=True)

    return {
        "profile": profile_data,
        "settings": settings_data,
        "capital": capital_data,
        "monthly_cash_flow": monthly_cash_flow,
        "expenses_from_savings": expenses_from_savings,
        "daily_income_tracker": daily_income_tracker,
        "remaining_capital": remaining_capital,
        "monthly_savings": monthly_savings,
        "total_savings": total_savings,
        "total_expenses_from_savings": total_expenses_from_savings,
        "net_savings": net_savings,
        "total_net_daily_income": total_net_daily_income,
        "calculate_net_income": calculate_net_income,
        "daily_income_by_month": sorted_months
    }

# --- Main Page Routes ---
@app.route('/')
def dashboard():
    return redirect(url_for('sources_page'))

@app.route('/sources')
def sources_page():
    data = get_all_financial_data()
    return render_template('sources.html', **data) if data else "Error", 500

@app.route('/capital')
def capital_page():
    data = get_all_financial_data()
    return render_template('capital.html', **data) if data else "Error", 500

@app.route('/savings')
def savings_page():
    data = get_all_financial_data()
    return render_template('savings.html', **data) if data else "Error", 500

@app.route('/daily_tracker')
def daily_tracker_page():
    data = get_all_financial_data()
    return render_template('daily_tracker.html', **data) if data else "Error", 500

@app.route('/monthly_summary')
def monthly_summary_page():
    data = get_all_financial_data()
    # Check which months have already been added to savings
    processed_months = {entry['month'] for entry in data.get('monthly_cash_flow', [])}
    return render_template('monthly_summary.html', processed_months=processed_months, **data) if data else "Error", 500

@app.route('/edit_sources', methods=['GET', 'POST'])
def edit_sources_page():
    data = get_all_financial_data()
    return render_template('edit_sources.html', **data) if data else "Error", 500

@app.route('/update_sources', methods=['POST'])
def update_sources():
    financial_data = load_financial_data()
    
    # Update source amounts
    for source in financial_data['capital']['sources']:
        source_name = source['name']
        if source_name in request.form:
            source['amount_bdt'] = int(request.form[source_name])
            
    # Update exchange rate
    financial_data['settings']['bdt_to_aud_rate'] = float(request.form['bdt_to_aud_rate'])
    
    save_financial_data(financial_data)
    return redirect(url_for('sources_page'))

# --- Add Routes ---
@app.route('/capital/add', methods=['POST'])
def add_capital_expense():
    financial_data = load_financial_data()
    new_expense = {"name": request.form['name'], "amount": float(request.form['amount'])}
    financial_data['capital']['expenses_from_capital'].append(new_expense)
    save_financial_data(financial_data)
    return redirect(url_for('capital_page'))

@app.route('/savings/add_monthly', methods=['POST'])
def add_monthly_entry():
    financial_data = load_financial_data()
    new_entry = {"month": request.form['month'], "income": float(request.form['income']), "loan_repayment": float(request.form['loan_repayment'])}
    financial_data['monthly_cash_flow'].append(new_entry)
    save_financial_data(financial_data)
    return redirect(url_for('savings_page'))

@app.route('/savings/add_lump_sum', methods=['POST'])
def add_lump_sum_monthly_income():
    financial_data = load_financial_data()
    
    year = request.form['year']
    month_num = request.form['month']
    month_key = f"{year}-{month_num}"
    gross_income = float(request.form['gross_income'])
    
    settings = financial_data.get('settings', {})
    tax_rate = settings.get('tax_rate_percent', 30.0)
    loan_repayment = settings.get('default_loan_repayment', 0)
    
    net_income_after_tax = calculate_net_income(gross_income, tax_rate)
    
    new_entry = {
        "month": month_key,
        "income": net_income_after_tax,
        "loan_repayment": loan_repayment
    }
    
    financial_data['monthly_cash_flow'].append(new_entry)
    save_financial_data(financial_data)
    
    return redirect(url_for('savings_page'))

@app.route('/savings/add_expense', methods=['POST'])
def add_saving_expense():
    financial_data = load_financial_data()
    new_expense = {"name": request.form['name'], "amount": float(request.form['amount'])}
    financial_data['expenses_from_savings'].append(new_expense)
    save_financial_data(financial_data)
    return redirect(url_for('savings_page'))

@app.route('/daily_tracker/add', methods=['POST'])
def add_daily_entry():
    financial_data = load_financial_data()
    new_entry = {"date": request.form['date'], "hours_worked": float(request.form['hours_worked']), "gross_income": float(request.form['gross_income'])}
    financial_data['daily_income_tracker'].append(new_entry)
    save_financial_data(financial_data)
    return redirect(url_for('daily_tracker_page'))

# --- Action Routes ---
@app.route('/process_month/<string:month_key>', methods=['POST'])
def process_month(month_key):
    financial_data = load_financial_data()
    
    # Recalculate the total net for the specific month to ensure accuracy
    daily_income_by_month = defaultdict(lambda: {'entries': [], 'total_net': 0})
    tax_rate = financial_data.get('settings', {}).get('tax_rate_percent', 30.0)
    for entry in financial_data.get('daily_income_tracker', []):
        try:
            current_month_key = datetime.strptime(entry['date'], '%Y-%m-%d').strftime('%Y-%m')
            if current_month_key == month_key:
                net_income = calculate_net_income(entry['gross_income'], tax_rate)
                daily_income_by_month[month_key]['total_net'] += net_income
        except ValueError:
            continue

    total_net_income_for_month = daily_income_by_month[month_key]['total_net']
    loan_repayment = financial_data.get('settings', {}).get('default_loan_repayment', 0)

    # Create a new entry for the monthly cash flow
    new_savings_entry = {
        "month": month_key,
        "income": total_net_income_for_month,
        "loan_repayment": loan_repayment
    }

    financial_data['monthly_cash_flow'].append(new_savings_entry)
    save_financial_data(financial_data)
    
    return redirect(url_for('monthly_summary_page'))

# --- Edit Routes ---
@app.route('/capital/edit/<int:index>', methods=['GET', 'POST'])
def edit_capital_expense(index):
    financial_data = load_financial_data()
    if request.method == 'POST':
        financial_data['capital']['expenses_from_capital'][index]['name'] = request.form['name']
        financial_data['capital']['expenses_from_capital'][index]['amount'] = float(request.form['amount'])
        save_financial_data(financial_data)
        return redirect(url_for('capital_page'))
    item = financial_data['capital']['expenses_from_capital'][index]
    return render_template('edit_capital_expense.html', expense=item, index=index)

@app.route('/savings/edit_monthly/<int:index>', methods=['GET', 'POST'])
def edit_monthly_entry(index):
    financial_data = load_financial_data()
    item = financial_data['monthly_cash_flow'][index]
    
    if request.method == 'POST':
        year = request.form['year']
        month_num = request.form['month']
        financial_data['monthly_cash_flow'][index]['month'] = f"{year}-{month_num}"
        financial_data['monthly_cash_flow'][index]['income'] = float(request.form['income'])
        financial_data['monthly_cash_flow'][index]['loan_repayment'] = float(request.form['loan_repayment'])
        save_financial_data(financial_data)
        return redirect(url_for('savings_page'))

    entry_year, entry_month = item['month'].split('-')
    return render_template('edit_monthly_entry.html', entry=item, index=index, entry_year=int(entry_year), entry_month=entry_month)

@app.route('/savings/edit_expense/<int:index>', methods=['GET', 'POST'])
def edit_savings_expense(index):
    financial_data = load_financial_data()
    if request.method == 'POST':
        financial_data['expenses_from_savings'][index]['name'] = request.form['name']
        financial_data['expenses_from_savings'][index]['amount'] = float(request.form['amount'])
        save_financial_data(financial_data)
        return redirect(url_for('savings_page'))
    item = financial_data['expenses_from_savings'][index]
    return render_template('edit_savings_expense.html', expense=item, index=index)

@app.route('/daily_tracker/edit/<int:index>', methods=['GET', 'POST'])
def edit_daily_entry(index):
    financial_data = load_financial_data()
    if request.method == 'POST':
        financial_data['daily_income_tracker'][index]['date'] = request.form['date']
        financial_data['daily_income_tracker'][index]['hours_worked'] = float(request.form['hours_worked'])
        financial_data['daily_income_tracker'][index]['gross_income'] = float(request.form['gross_income'])
        save_financial_data(financial_data)
        return redirect(url_for('daily_tracker_page'))
    item = financial_data['daily_income_tracker'][index]
    return render_template('edit_daily_entry.html', entry=item, index=index)

# --- Delete Route ---
@app.route('/delete/<string:list_name>/<int:index>')
def delete_item(list_name, index):
    financial_data = load_financial_data()
    
    target_list = None
    redirect_page = None
    if list_name == 'capital_expenses':
        target_list = financial_data['capital']['expenses_from_capital']
        redirect_page = 'capital_page'
    elif list_name == 'monthly_cash_flow':
        target_list = financial_data['monthly_cash_flow']
        redirect_page = 'savings_page'
    elif list_name == 'expenses_from_savings':
        target_list = financial_data['expenses_from_savings']
        redirect_page = 'savings_page'
    elif list_name == 'daily_income_tracker':
        target_list = financial_data['daily_income_tracker']
        redirect_page = 'daily_tracker_page'

    if target_list is not None and 0 <= index < len(target_list):
        target_list.pop(index)
        save_financial_data(financial_data)
        return redirect(url_for(redirect_page))
    
    return "Error: List not found or index out of bounds", 404

# --- Settings Update ---
@app.route('/settings/update_tax', methods=['POST'])
def update_tax_rate():
    financial_data = load_financial_data()
    financial_data['settings']['tax_rate_percent'] = float(request.form['tax_rate'])
    save_financial_data(financial_data)
    return redirect(url_for('daily_tracker_page'))

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
