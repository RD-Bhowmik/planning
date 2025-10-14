# Environment Variables

## Vercel (Production)

**Automatically set when you connect Vercel Postgres:**
- `POSTGRES_URL` - Set automatically by Vercel
- `VERCEL` - Set automatically by Vercel
- `VERCEL_ENV` - Set automatically by Vercel

No manual configuration needed!

## Local Development

Leave environment variables empty - app will use SQLite automatically.

Optional for local development:
```bash
SECRET_KEY=your-local-secret-key
```

## Testing with PostgreSQL Locally

If you want to test PostgreSQL locally (optional):
```bash
POSTGRES_URL=postgresql://user:password@localhost:5432/dbname
```
