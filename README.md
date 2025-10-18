# Personal Financial Planning Web Application

A comprehensive financial management web application designed to help users track their finances, particularly for international students or immigrants planning to move abroad. The application provides real-time currency conversion, capital tracking, monthly savings management, and loan progress monitoring.

## 🌟 Key Features

### Multi-Currency Financial Management

- **Real-time Currency Conversion**: Live exchange rate integration from BDT to 19+ international currencies
- **Popular Destinations Support**: Australia, USA, New Zealand, UK, Canada, EU, Singapore, Malaysia, Japan, and more
- **Exchange Rate API Integration**: Automatic rate updates using ExchangeRate-API.com

### Comprehensive Financial Tracking

- **Capital Sources Management**: Track initial funding from parents, loans, personal savings
- **Monthly Cash Flow**: Monitor income, loan repayments, and savings with detailed analytics
- **Daily Income Tracker**: Log daily work hours and income with automatic tax calculations
- **Expense Management**: Track expenses from both capital and savings with categorization
- **Loan Management**: Monitor loan progress, remaining balance, and repayment schedules

### User Experience

- **Secure Authentication**: User registration and login system with password hashing
- **Guest Mode**: Trial access without registration requirements
- **Responsive Design**: Mobile-optimized interface with smooth animations
- **Real-time Updates**: Live data synchronization and instant calculations

## 🛠️ Technical Architecture

### Backend Technologies

- **Python Flask** - Web framework and API development
- **PostgreSQL/SQLite** - Database management with connection pooling
- **Flask-Login** - User authentication and session management
- **bcrypt** - Password hashing and security
- **psycopg2** - PostgreSQL database adapter
- **Waitress** - WSGI server for production deployment

### Frontend Technologies

- **HTML5/CSS3** - Responsive web design with custom styling
- **Bootstrap 5** - UI framework with enhanced components
- **JavaScript** - Dynamic interactions and API calls
- **Jinja2 Templates** - Server-side templating engine

### External Integrations

- **ExchangeRate-API** - Real-time currency conversion service
- **Vercel** - Cloud deployment and serverless functions

### Key Technical Features

- **Database Connection Pooling** - Optimized database performance and resource management
- **Modular Architecture** - Separated concerns with dedicated modules for maintainability
- **RESTful API Design** - Clean API endpoints for data operations
- **Responsive Design** - Mobile-first approach with cross-device compatibility
- **Real-time Data Updates** - Live currency rate fetching with caching
- **Data Validation** - Comprehensive input sanitization and error handling
- **Security Implementation** - Password hashing, session management, and input validation

## 📁 Project Structure

```
planning/
├── api/                    # Vercel serverless functions
│   └── index.py           # Main API entry point
├── data/                   # Database files and JSON storage
│   ├── financial_plan.json
│   ├── user_1.json
│   ├── user_2.json
│   └── users.db
├── modules/                # Core business logic modules
│   ├── __init__.py
│   ├── auth_manager.py     # User authentication and management
│   ├── calculations.py     # Financial calculations and formulas
│   ├── cache.py           # Caching mechanisms
│   ├── data_manager.py     # Data persistence layer
│   ├── db_config.py       # Database configuration
│   ├── db_pool.py         # Connection pooling
│   ├── exchange_rate_api.py # Currency API integration
│   └── financial_db.py     # Database operations
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── capital.html       # Capital sources page
│   ├── daily_tracker.html # Daily income tracking
│   ├── login.html         # Authentication pages
│   ├── monthly_summary.html # Monthly analytics
│   ├── savings.html       # Savings management
│   └── sources.html       # Capital sources management
├── main.py                 # Flask application entry point
├── requirements.txt        # Python dependencies
├── vercel.json            # Vercel deployment configuration
└── README.md              # Project documentation
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL (optional, SQLite supported)
- Git

### Local Development

1. **Clone the repository**

   ```bash
   git clone https://github.com/RD-Bhowmik/planning.git
   cd planning
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   ```bash
   # Create .env file
   DATABASE_URL=postgresql://username:password@localhost/planning_db
   SECRET_KEY=your-secret-key-here
   ```

4. **Initialize database**

   ```bash
   python main.py
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

### Production Deployment (Vercel)

1. **Deploy to Vercel**

   ```bash
   vercel --prod
   ```

2. **Configure environment variables in Vercel dashboard**
   - `DATABASE_URL`: PostgreSQL connection string
   - `SECRET_KEY`: Flask secret key

## 📊 Database Schema

### Users Table

- `id` - Primary key
- `username` - Unique username
- `email` - Unique email address
- `password_hash` - Bcrypt hashed password
- `created_at` - Account creation timestamp

### Financial Data Structure

- **Profile**: User personal information
- **Settings**: Currency preferences, tax rates, loan settings
- **Capital**: Initial funding sources and expenses
- **Monthly Cash Flow**: Income and loan repayment tracking
- **Daily Income Tracker**: Daily work and income logging
- **Expenses from Savings**: Savings-based expense tracking

## 🔧 API Endpoints

### Authentication

- `POST /login` - User login
- `POST /signup` - User registration
- `GET /logout` - User logout
- `GET /guest` - Guest mode access

### Financial Management

- `GET /sources` - Capital sources overview
- `GET /capital` - Capital management
- `GET /savings` - Savings tracking
- `GET /daily_tracker` - Daily income logging
- `GET /monthly_summary` - Monthly analytics
- `GET /loan` - Loan management

### Data Operations

- `POST /update_sources` - Update capital sources
- `POST /capital/add` - Add capital expenses
- `POST /savings/add_monthly` - Add monthly entries
- `POST /daily_tracker/add` - Add daily income entries
- `POST /api/fetch_exchange_rate` - Fetch live exchange rates

## 🌐 Live Application

**Production URL**: [planning-phi.vercel.app](https://planning-phi.vercel.app)

## 🎯 CV-Ready Project Summary

### Project Title

**Personal Financial Planning Web Application**

### Project Description

Developed a comprehensive financial management web application using Python Flask and PostgreSQL, designed to help international students and immigrants track their finances across multiple currencies. The application features real-time currency conversion, secure user authentication, and comprehensive financial tracking including capital management, monthly cash flow, daily income logging, and loan progress monitoring.

### Key Achievements

- **Real-time Currency Integration**: Implemented live exchange rate updates supporting 19+ international currencies
- **Secure Authentication System**: Built user registration and login with bcrypt password hashing and session management
- **Responsive UI/UX**: Designed mobile-first interface with Bootstrap 5 and custom CSS animations
- **Scalable Database Design**: Implemented dual database support (PostgreSQL/SQLite) with connection pooling
- **Modular Architecture**: Created maintainable codebase with separated concerns and dedicated modules
- **Cloud Deployment**: Successfully deployed production-ready application on Vercel with serverless functions
- **API Integration**: Integrated external currency exchange API with error handling and caching

### Technical Skills Demonstrated

- **Backend Development**: Python, Flask, RESTful API design, database management
- **Frontend Development**: HTML5, CSS3, JavaScript, Bootstrap 5, responsive design
- **Database Management**: PostgreSQL, SQLite, connection pooling, data modeling
- **Security**: Password hashing, session management, input validation
- **Cloud Technologies**: Vercel deployment, serverless functions, environment configuration
- **API Integration**: External API consumption, error handling, data processing
- **Version Control**: Git, GitHub repository management

### Technologies Used

**Backend**: Python, Flask, PostgreSQL, SQLite, bcrypt, psycopg2, Waitress
**Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Jinja2
**External Services**: ExchangeRate-API, Vercel
**Tools**: Git, GitHub, Vercel CLI

## 📈 Future Enhancements

- [ ] Advanced financial analytics and reporting
- [ ] Mobile app development (React Native/Flutter)
- [ ] Investment tracking and portfolio management
- [ ] Budget planning and forecasting tools
- [ ] Multi-language support
- [ ] Advanced data visualization with charts and graphs
- [ ] Export functionality (PDF reports, Excel spreadsheets)
- [ ] Integration with banking APIs for automatic transaction import

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Author

**RD-Bhowmik**

- GitHub: [@RD-Bhowmik](https://github.com/RD-Bhowmik)
- Project Link: [https://github.com/RD-Bhowmik/planning](https://github.com/RD-Bhowmik/planning)

---

_This project demonstrates full-stack web development skills, database design, API integration, user authentication, responsive design, and cloud deployment - making it an excellent addition to any software developer's portfolio._
