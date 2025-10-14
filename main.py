
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from collections import defaultdict
from datetime import datetime
from waitress import serve
import os
import secrets
from modules.data_manager import load_financial_data, save_financial_data, get_default_financial_data
from modules.calculations import (
    calculate_remaining_capital,
    calculate_monthly_savings,
    calculate_total_savings,
    calculate_total_expenses_from_savings,
    calculate_net_income,
    calculate_total_daily_net_income
)
from modules.exchange_rate_api import ExchangeRateAPI
from modules.auth_manager import (
    init_db, 
    create_user, 
    verify_user, 
    get_user_by_id
)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# Initialize database
init_db()

# Initialize financial data tables (for PostgreSQL)
from modules.financial_db import init_financial_tables
init_financial_tables()

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

def get_currency_rate(settings_data):
    """Get the exchange rate for the selected target currency"""
    target_currency = settings_data.get('target_currency', 'AUD')
    
    # Default rates (will be updated by API)
    rate_map = {
        'AUD': settings_data.get('bdt_to_aud_rate', 0.0127),
        'USD': settings_data.get('bdt_to_usd_rate', 0.0091),
        'NZD': settings_data.get('bdt_to_nzd_rate', 0.0135),
        'GBP': settings_data.get('bdt_to_gbp_rate', 0.0072),
        'CAD': settings_data.get('bdt_to_cad_rate', 0.0124),
        'EUR': settings_data.get('bdt_to_eur_rate', 0.0085),
        'SGD': settings_data.get('bdt_to_sgd_rate', 0.0122),
        'MYR': settings_data.get('bdt_to_myr_rate', 0.0411),
        'JPY': settings_data.get('bdt_to_jpy_rate', 1.35),
        'KRW': settings_data.get('bdt_to_krw_rate', 12.10),
        'CNY': settings_data.get('bdt_to_cny_rate', 0.066),
        'INR': settings_data.get('bdt_to_inr_rate', 0.76),
        'THB': settings_data.get('bdt_to_thb_rate', 0.31),
        'CHF': settings_data.get('bdt_to_chf_rate', 0.0081),
        'SEK': settings_data.get('bdt_to_sek_rate', 0.095),
        'NOK': settings_data.get('bdt_to_nok_rate', 0.098),
        'DKK': settings_data.get('bdt_to_dkk_rate', 0.063),
        'AED': settings_data.get('bdt_to_aed_rate', 0.033),
        'SAR': settings_data.get('bdt_to_sar_rate', 0.034)
    }
    
    return rate_map.get(target_currency, 0.0127), target_currency

def get_all_financial_data():
    """Load financial data based on user authentication status"""
    # Check if user is logged in
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        # Guest user - load from session
        guest_data = session.get('guest_financial_data')
        financial_data = load_financial_data(is_guest=True, guest_data=guest_data)
    
    if not financial_data:
        return None

    profile_data = financial_data.get('profile', {})
    settings_data = financial_data.get('settings', {})
    capital_data = financial_data.get('capital', {})
    monthly_cash_flow = financial_data.get('monthly_cash_flow', [])
    expenses_from_savings = financial_data.get('expenses_from_savings', [])
    daily_income_tracker = financial_data.get('daily_income_tracker', [])
    tax_rate = settings_data.get('tax_rate_percent', 30.0)

    # Get rate based on selected currency
    bdt_rate, target_currency = get_currency_rate(settings_data)
    settings_data['current_rate'] = bdt_rate
    settings_data['target_currency'] = target_currency

    # Convert BDT sources to AUD and calculate total capital
    total_capital_aud = 0
    loan_data = None
    for source in capital_data.get('sources', []):
        source['amount_aud'] = source.get('amount_bdt', 0) * bdt_rate
        total_capital_aud += source['amount_aud']
        # Extract loan data separately
        if source.get('name', '').lower() == 'loan':
            loan_data = {
                'amount_bdt': source.get('amount_bdt', 0),
                'amount_aud': source['amount_aud']
            }
    capital_data['total_capital_aud'] = total_capital_aud
    
    # Calculate loan statistics
    if loan_data:
        total_loan_paid = sum(entry.get('loan_repayment', 0) for entry in monthly_cash_flow)
        loan_payment_count = len(monthly_cash_flow)
        remaining_loan_balance = max(0, loan_data['amount_aud'] - total_loan_paid)
        
        # Calculate progress percentage
        if loan_data['amount_aud'] > 0:
            loan_progress_percent = (total_loan_paid / loan_data['amount_aud']) * 100
        else:
            loan_progress_percent = 0
        
        # Calculate months remaining
        monthly_repayment = settings_data.get('default_loan_repayment', 0)
        if monthly_repayment > 0 and remaining_loan_balance > 0:
            months_remaining = int(remaining_loan_balance / monthly_repayment) + 1
        else:
            months_remaining = 0
    else:
        # Default values if no loan found
        loan_data = {'amount_bdt': 0, 'amount_aud': 0}
        total_loan_paid = 0
        loan_payment_count = 0
        remaining_loan_balance = 0
        loan_progress_percent = 0
        months_remaining = 0

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

    # Sort months chronologically based on user preference
    sort_order = settings_data.get('table_sort_order', 'newest_first')
    sorted_months = sorted(daily_income_by_month.items(), key=lambda item: item[0], reverse=(sort_order == 'newest_first'))

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
        "daily_income_by_month": sorted_months,
        "loan_data": loan_data,
        "total_loan_paid": total_loan_paid,
        "loan_payment_count": loan_payment_count,
        "remaining_loan_balance": remaining_loan_balance,
        "loan_progress_percent": loan_progress_percent,
        "months_remaining": months_remaining
    }

def save_user_financial_data(financial_data):
    """Save financial data based on user authentication status"""
    if current_user.is_authenticated:
        # Logged-in user - save to their file
        save_financial_data(financial_data, user_id=current_user.id)
    else:
        # Guest user - save to session
        session['guest_financial_data'] = financial_data
        save_financial_data(financial_data, is_guest=True)

# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('sources_page'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, result = verify_user(username, password)
        
        if success:
            login_user(result)
            flash('Welcome back! You have been successfully logged in.', 'success')
            
            # Check if there's guest data to migrate
            guest_data = session.get('guest_financial_data')
            if guest_data:
                # Ask user if they want to keep guest data or load their saved data
                session['pending_guest_data'] = guest_data
            
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('sources_page'))
        else:
            return render_template('login.html', error=result)
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # If already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('sources_page'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate passwords match
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')
        
        # Validate password length
        if len(password) < 6:
            return render_template('signup.html', error='Password must be at least 6 characters long')
        
        # Validate username length
        if len(username) < 3:
            return render_template('signup.html', error='Username must be at least 3 characters long')
        
        success, result = create_user(username, email, password)
        
        if success:
            # Log the user in automatically
            user_success, user = verify_user(username, password)
            if user_success:
                login_user(user)
                
                # Migrate guest data if exists
                guest_data = session.get('guest_financial_data')
                if guest_data:
                    save_financial_data(guest_data, user_id=user.id)
                    session.pop('guest_financial_data', None)
                
                flash('Account created successfully! Welcome aboard!', 'success')
                return redirect(url_for('sources_page'))
        else:
            return render_template('signup.html', error=result)
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/guest')
def guest_mode():
    """Initialize guest mode with empty data"""
    if 'guest_financial_data' not in session:
        session['guest_financial_data'] = get_default_financial_data()
    return redirect(url_for('sources_page'))

# --- Main Page Routes ---
@app.route('/')
def dashboard():
    return redirect(url_for('sources_page'))

@app.route('/sources')
def sources_page():
    data = get_all_financial_data()
    return render_template('sources.html', **data) if data else make_response("Error loading financial data", 500)

@app.route('/capital')
def capital_page():
    data = get_all_financial_data()
    return render_template('capital.html', **data) if data else make_response("Error loading financial data", 500)

@app.route('/savings')
def savings_page():
    data = get_all_financial_data()
    return render_template('savings.html', **data) if data else make_response("Error loading financial data", 500)

@app.route('/daily_tracker')
def daily_tracker_page():
    data = get_all_financial_data()
    return render_template('daily_tracker.html', **data) if data else make_response("Error loading financial data", 500)

@app.route('/monthly_summary')
def monthly_summary_page():
    data = get_all_financial_data()
    # Check which months have already been added to savings
    processed_months = {entry['month'] for entry in data.get('monthly_cash_flow', [])}
    return render_template('monthly_summary.html', processed_months=processed_months, **data) if data else make_response("Error loading financial data", 500)

@app.route('/edit_sources', methods=['GET', 'POST'])
def edit_sources_page():
    data = get_all_financial_data()
    return render_template('edit_sources.html', **data) if data else make_response("Error loading financial data", 500)

@app.route('/update_sources', methods=['POST'])
def update_sources():
    # Get financial data based on user type
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
    print("="*50)
    print("UPDATE SOURCES - Backend Debug")
    print("="*50)
    print(f"All form keys: {list(request.form.keys())}")
    
    # Collect all sources from form data
    new_sources = []
    index = 0
    while f'source_name_{index}' in request.form:
        name = request.form.get(f'source_name_{index}')
        amount_bdt = request.form.get(f'source_amount_{index}')
        
        print(f"Index {index}: name='{name}', amount='{amount_bdt}'")
        
        if name and amount_bdt:
            new_sources.append({
                'name': name,
                'amount_bdt': int(amount_bdt)
            })
        index += 1
    
    print(f"\nFinal result: {len(new_sources)} sources collected")
    for i, source in enumerate(new_sources):
        print(f"  Source {i}: {source['name']} = {source['amount_bdt']} BDT")
    
    print(f"\nOld sources count: {len(financial_data['capital']['sources'])}")
    
    # Update sources in financial data
    financial_data['capital']['sources'] = new_sources
    
    print(f"New sources count: {len(financial_data['capital']['sources'])}")
            
    # Update exchange rate
    financial_data['settings']['bdt_to_aud_rate'] = float(request.form['bdt_to_aud_rate'])
    
    save_user_financial_data(financial_data)
    print("Data saved successfully!")
    print("="*50)
    
    flash(f'Capital sources updated successfully! ({len(new_sources)} sources saved)', 'success')
    return redirect(url_for('sources_page'))

# --- Add Routes ---
@app.route('/capital/add', methods=['POST'])
def add_capital_expense():
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    new_expense = {"name": request.form['name'], "amount": float(request.form['amount'])}
    financial_data['capital']['expenses_from_capital'].append(new_expense)
    save_user_financial_data(financial_data)
    return redirect(url_for('capital_page'))

@app.route('/savings/add_monthly', methods=['POST'])
def add_monthly_entry():
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    new_entry = {"month": request.form['month'], "income": float(request.form['income']), "loan_repayment": float(request.form['loan_repayment'])}
    financial_data['monthly_cash_flow'].append(new_entry)
    save_user_financial_data(financial_data)
    return redirect(url_for('savings_page'))

@app.route('/savings/add_lump_sum', methods=['POST'])
def add_lump_sum_monthly_income():
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
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
    save_user_financial_data(financial_data)
    
    return redirect(url_for('savings_page'))

@app.route('/savings/add_expense', methods=['POST'])
def add_saving_expense():
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    new_expense = {"name": request.form['name'], "amount": float(request.form['amount'])}
    financial_data['expenses_from_savings'].append(new_expense)
    save_user_financial_data(financial_data)
    return redirect(url_for('savings_page'))

@app.route('/daily_tracker/add', methods=['POST'])
def add_daily_entry():
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    new_entry = {"date": request.form['date'], "hours_worked": float(request.form['hours_worked']), "gross_income": float(request.form['gross_income'])}
    financial_data['daily_income_tracker'].append(new_entry)
    save_user_financial_data(financial_data)
    return redirect(url_for('daily_tracker_page'))

# --- Action Routes ---
@app.route('/process_month/<string:month_key>', methods=['POST'])
def process_month(month_key):
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
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
    save_user_financial_data(financial_data)
    
    return redirect(url_for('monthly_summary_page'))

# --- Edit Routes ---
@app.route('/capital/edit/<int:index>', methods=['GET', 'POST'])
def edit_capital_expense(index):
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    if request.method == 'POST':
        financial_data['capital']['expenses_from_capital'][index]['name'] = request.form['name']
        financial_data['capital']['expenses_from_capital'][index]['amount'] = float(request.form['amount'])
        save_user_financial_data(financial_data)
        return redirect(url_for('capital_page'))
    item = financial_data['capital']['expenses_from_capital'][index]
    return render_template('edit_capital_expense.html', expense=item, index=index)

@app.route('/savings/edit_monthly/<int:index>', methods=['GET', 'POST'])
def edit_monthly_entry(index):
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    item = financial_data['monthly_cash_flow'][index]
    
    if request.method == 'POST':
        year = request.form['year']
        month_num = request.form['month']
        financial_data['monthly_cash_flow'][index]['month'] = f"{year}-{month_num}"
        financial_data['monthly_cash_flow'][index]['income'] = float(request.form['income'])
        financial_data['monthly_cash_flow'][index]['loan_repayment'] = float(request.form['loan_repayment'])
        save_user_financial_data(financial_data)
        return redirect(url_for('savings_page'))

    entry_year, entry_month = item['month'].split('-')
    return render_template('edit_monthly_entry.html', entry=item, index=index, entry_year=int(entry_year), entry_month=entry_month)

@app.route('/savings/edit_by_month/<string:month>', methods=['GET', 'POST'])
def edit_monthly_entry_by_month(month):
    """Edit monthly cash flow entry by month identifier"""
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
    # Find the entry with matching month
    monthly_cash_flow = financial_data['monthly_cash_flow']
    entry_index = None
    item = None
    
    for i, entry in enumerate(monthly_cash_flow):
        if entry['month'] == month:
            entry_index = i
            item = entry
            break
    
    if item is None:
        flash(f'Entry not found for {month}', 'error')
        return redirect(url_for('savings_page'))
    
    if request.method == 'POST':
        year = request.form['year']
        month_num = request.form['month']
        financial_data['monthly_cash_flow'][entry_index]['month'] = f"{year}-{month_num}"
        financial_data['monthly_cash_flow'][entry_index]['income'] = float(request.form['income'])
        financial_data['monthly_cash_flow'][entry_index]['loan_repayment'] = float(request.form['loan_repayment'])
        save_user_financial_data(financial_data)
        flash(f'Monthly entry updated successfully!', 'success')
        return redirect(url_for('savings_page'))

    entry_year, entry_month = item['month'].split('-')
    return render_template('edit_monthly_entry.html', entry=item, index=entry_index, entry_year=int(entry_year), entry_month=entry_month)

@app.route('/savings/edit_expense/<int:index>', methods=['GET', 'POST'])
def edit_savings_expense(index):
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    if request.method == 'POST':
        financial_data['expenses_from_savings'][index]['name'] = request.form['name']
        financial_data['expenses_from_savings'][index]['amount'] = float(request.form['amount'])
        save_user_financial_data(financial_data)
        return redirect(url_for('savings_page'))
    item = financial_data['expenses_from_savings'][index]
    return render_template('edit_savings_expense.html', expense=item, index=index)

@app.route('/daily_tracker/edit/<int:index>', methods=['GET', 'POST'])
def edit_daily_entry(index):
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    if request.method == 'POST':
        financial_data['daily_income_tracker'][index]['date'] = request.form['date']
        financial_data['daily_income_tracker'][index]['hours_worked'] = float(request.form['hours_worked'])
        financial_data['daily_income_tracker'][index]['gross_income'] = float(request.form['gross_income'])
        save_user_financial_data(financial_data)
        return redirect(url_for('daily_tracker_page'))
    item = financial_data['daily_income_tracker'][index]
    return render_template('edit_daily_entry.html', entry=item, index=index)

# --- Delete Route ---
@app.route('/delete/<string:list_name>/<int:index>')
def delete_item(list_name, index):
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
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
        save_user_financial_data(financial_data)
        return redirect(url_for(redirect_page))
    
    return "Error: List not found or index out of bounds", 404

# --- Delete by identifier (for sorted lists) ---
@app.route('/delete_by_month/<string:month>')
def delete_by_month(month):
    """Delete monthly cash flow entry by month identifier"""
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
    # Find and remove the entry with matching month
    monthly_cash_flow = financial_data['monthly_cash_flow']
    original_length = len(monthly_cash_flow)
    
    # Remove entry with matching month
    financial_data['monthly_cash_flow'] = [entry for entry in monthly_cash_flow if entry['month'] != month]
    
    if len(financial_data['monthly_cash_flow']) < original_length:
        save_user_financial_data(financial_data)
        flash(f'Monthly entry for {month} deleted successfully!', 'success')
    else:
        flash(f'Entry not found for {month}', 'error')
    
    return redirect(url_for('savings_page'))

# --- Loan Management Routes ---
@app.route('/loan')
def loan_page():
    data = get_all_financial_data()
    return render_template('loan_management.html', **data) if data else make_response("Error loading financial data", 500)

@app.route('/loan/edit')
def edit_loan_page():
    data = get_all_financial_data()
    return render_template('edit_loan.html', **data) if data else make_response("Error loading financial data", 500)

@app.route('/loan/update', methods=['POST'])
def update_loan():
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
    # Get loan amount from form
    loan_amount_bdt = int(request.form['loan_amount_bdt'])
    
    # Find and update the loan source (case-insensitive)
    loan_found = False
    for source in financial_data['capital']['sources']:
        if source.get('name', '').lower() == 'loan':
            source['amount_bdt'] = loan_amount_bdt
            loan_found = True
            print(f"Updated existing loan source: {loan_amount_bdt} BDT")
            break
    
    # If no loan source exists, create one
    if not loan_found:
        financial_data['capital']['sources'].append({
            'name': 'Loan',
            'amount_bdt': loan_amount_bdt
        })
        print(f"Created new loan source: {loan_amount_bdt} BDT")
    
    # Update loan details in settings
    financial_data['settings']['default_loan_repayment'] = float(request.form['loan_repayment'])
    financial_data['settings']['loan_interest_rate'] = float(request.form.get('loan_interest_rate', 0))
    financial_data['settings']['loan_period_months'] = int(request.form.get('loan_period_months', 12))
    
    # Save changes
    save_user_financial_data(financial_data)
    flash('Loan details updated successfully!', 'success')
    return redirect(url_for('loan_page'))

# --- Currency Selection Route ---
@app.route('/set_currency/<string:currency>', methods=['POST'])
def set_currency(currency):
    """Change target currency"""
    valid_currencies = ['AUD', 'USD', 'NZD', 'GBP', 'CAD', 'EUR', 'SGD', 'MYR', 
                       'JPY', 'KRW', 'CNY', 'INR', 'THB', 'CHF', 'SEK', 'NOK', 
                       'DKK', 'AED', 'SAR']
    
    if currency not in valid_currencies:
        return jsonify({'success': False, 'error': 'Invalid currency'}), 400
    
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
    financial_data['settings']['target_currency'] = currency
    save_user_financial_data(financial_data)
    
    flash(f'Currency changed to {currency} successfully!', 'success')
    return jsonify({'success': True, 'currency': currency})

# --- Exchange Rate API Routes ---
@app.route('/api/fetch_exchange_rate', methods=['POST'])
def fetch_exchange_rate():
    """API endpoint to fetch current exchange rate for selected currency"""
    # Get current financial data to know target currency
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
    target_currency = financial_data['settings'].get('target_currency', 'AUD')
    
    # Fetch all three rates
    currencies = ['AUD', 'USD', 'NZD']
    results = {}
    
    for currency in currencies:
        result = ExchangeRateAPI.fetch_rate(from_currency='BDT', to_currency=currency)
        if result.get('success'):
            rate_key = f'bdt_to_{currency.lower()}_rate'
            financial_data['settings'][rate_key] = result['rate']
            results[currency] = result['rate']
    
    # Update timestamp
    financial_data['settings']['exchange_rate_last_updated'] = datetime.now().isoformat()
    financial_data['settings']['exchange_rate_source'] = 'ExchangeRate-API'
    save_user_financial_data(financial_data)
    
    if results:
        return jsonify({
            'success': True,
            'rates': results,
            'current_currency': target_currency,
            'current_rate': results.get(target_currency, 0),
            'timestamp': financial_data['settings']['exchange_rate_last_updated'],
            'formatted_time': ExchangeRateAPI.format_timestamp(financial_data['settings']['exchange_rate_last_updated'])
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch exchange rates'
        }), 400

# --- Settings Update ---
@app.route('/settings/update_tax', methods=['POST'])
def update_tax_rate():
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    financial_data['settings']['tax_rate_percent'] = float(request.form['tax_rate'])
    save_user_financial_data(financial_data)
    return redirect(url_for('daily_tracker_page'))

@app.route('/settings/update_sort_order', methods=['POST'])
def update_sort_order():
    """Update table sort order preference"""
    if current_user.is_authenticated:
        financial_data = load_financial_data(user_id=current_user.id)
    else:
        financial_data = load_financial_data(is_guest=True, guest_data=session.get('guest_financial_data'))
    
    sort_order = request.form.get('sort_order', 'newest_first')
    financial_data['settings']['table_sort_order'] = sort_order
    save_user_financial_data(financial_data)
    
    flash(f'Table sort order updated to {"newest first" if sort_order == "newest_first" else "oldest first"}!', 'success')
    
    # Redirect back to the referring page
    return redirect(request.referrer or url_for('dashboard'))

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
