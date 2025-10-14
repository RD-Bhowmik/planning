# Vercel PostgreSQL Setup Guide

## ✅ What's Been Done

Your app now supports **Vercel Postgres** with automatic fallback to SQLite for local development!

### Changes Made:

1. ✅ Added PostgreSQL support (`psycopg2-binary`)
2. ✅ Created dual-mode database system (Postgres + SQLite)
3. ✅ Updated auth system to work with both databases
4. ✅ Updated financial data storage to use PostgreSQL
5. ✅ Automatic environment detection

## 🚀 Deployment Steps

### Step 1: Create Vercel Postgres Database

1. **Go to your Vercel project dashboard**

   ```
   https://vercel.com/your-username/planning
   ```

2. **Navigate to Storage tab**

   - Click "Storage" in the top menu
   - Click "Create Database"
   - Select "Postgres"

3. **Create the database**

   - Database name: `planning-db` (or any name you prefer)
   - Region: Choose closest to your users
   - Click "Create"

4. **Connect to your project**
   - Vercel will show you the database
   - Click "Connect Project"
   - Select your `planning` project
   - Click "Connect"

### Step 2: Environment Variables (Automatic!)

Vercel **automatically** sets these environment variables when you connect the database:

- `POSTGRES_URL` - Full connection string
- `POSTGRES_PRISMA_URL` - Prisma connection string
- `POSTGRES_URL_NON_POOLING` - Non-pooling connection
- `POSTGRES_USER` - Database user
- `POSTGRES_HOST` - Database host
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_DATABASE` - Database name

**You don't need to set anything manually!** ✨

### Step 3: Deploy

```bash
cd /home/ronodeep/planning

# Make sure all changes are committed
git add .
git commit -m "Add PostgreSQL support for Vercel"

# Push to deploy
git push origin main
```

Vercel will automatically deploy with PostgreSQL!

### Step 4: Verify

1. **Check deployment logs**

   ```
   https://vercel.com/your-username/planning/deployments
   ```

2. **Look for these messages:**

   ```
   ✓ Using PostgreSQL database
   ✓ Database initialized successfully (postgres)
   ✓ Financial tables initialized (PostgreSQL)
   ```

3. **Test your app:**
   - Create an account → Should work!
   - Add sources → Should persist!
   - Refresh page → Data should still be there!

## 🏠 Local Development

Your app still works locally with SQLite (no changes needed):

```bash
python main.py
```

It will automatically use `data/users.db` and JSON files locally.

## 🔍 How It Works

### Automatic Detection:

```python
# In db_config.py
if os.environ.get('POSTGRES_URL'):
    # Use PostgreSQL (Vercel production)
    DB_TYPE = 'postgres'
else:
    # Use SQLite (local development)
    DB_TYPE = 'sqlite'
```

### Database Structure:

**Users Table:**

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
)
```

**Financial Data Table:**

```sql
CREATE TABLE financial_data (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    profile JSONB,
    settings JSONB,
    capital JSONB,
    monthly_cash_flow JSONB,
    expenses_from_savings JSONB,
    daily_income_tracker JSONB,
    updated_at TIMESTAMP
)
```

## 📊 Benefits

### Before (SQLite + JSON):

- ❌ Data lost every 5-15 minutes on Vercel
- ❌ Read-only filesystem errors
- ❌ Not production-ready

### After (PostgreSQL):

- ✅ Data persists permanently
- ✅ Scalable to thousands of users
- ✅ ACID compliance (data integrity)
- ✅ Automatic backups by Vercel
- ✅ Free tier: 256MB storage, 60 hours compute/month

## 🧪 Testing Checklist

After deployment, test these:

- [ ] Visit your Vercel URL
- [ ] Create a new account
- [ ] Login with your account
- [ ] Add 3 capital sources
- [ ] Edit and remove one source
- [ ] Add some expenses
- [ ] Logout and login again
- [ ] **Verify all data is still there!** ✅

## 📝 Database Management

### View Data (Vercel Dashboard):

1. Go to Storage → Your Database
2. Click "Query" tab
3. Run SQL queries:

```sql
-- See all users
SELECT id, username, email, created_at FROM users;

-- See specific user's data
SELECT * FROM financial_data WHERE user_id = 1;

-- Count users
SELECT COUNT(*) FROM users;
```

### Backup:

Vercel automatically backs up your database. You can also:

1. Go to Storage → Database → Settings
2. Click "Backups"
3. Download backup or restore

## 🐛 Troubleshooting

### Error: "relation 'users' does not exist"

**Solution:** Database tables not initialized

```bash
# The app should auto-create tables on first run
# If not, check deployment logs for errors
```

### Error: "could not connect to server"

**Solution:** Database not connected to project

- Go to Vercel → Storage → Your Database
- Click "Connect Project"
- Select your project

### Data not persisting

**Solution:** Check environment variables

- Vercel → Project → Settings → Environment Variables
- Ensure `POSTGRES_URL` is set

### Works locally but not on Vercel

**Solution:** Check deployment logs

```bash
vercel logs your-deployment-url
```

## 🎉 You're Done!

Your app now has:

- ✅ Persistent data storage (PostgreSQL)
- ✅ User authentication
- ✅ Local development support (SQLite)
- ✅ Production-ready architecture
- ✅ Automatic environment detection

## 📚 Additional Resources

- [Vercel Postgres Documentation](https://vercel.com/docs/storage/vercel-postgres)
- [PostgreSQL JSON Functions](https://www.postgresql.org/docs/current/functions-json.html)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

---

**Need Help?** Check the deployment logs or contact support!
