# BookNest Deployment Guide

## Vercel Deployment

### Prerequisites

- A [Vercel](https://vercel.com) account
- The [Vercel CLI](https://vercel.com/docs/cli) installed (`npm i -g vercel`)
- Python 3.11+ configured in your project

---

### Project Structure

```
booknest/
├── app/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── routers/
│   ├── templates/
│   └── main.py
├── requirements.txt
├── vercel.json
└── DEPLOYMENT.md
```

---

### vercel.json Configuration

Create a `vercel.json` file in the project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "app/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

> **Note:** Vercel's Python runtime expects the ASGI/WSGI app object. Ensure `app/main.py` exposes the FastAPI instance as `app`.

---

### Environment Variables

Set the following environment variables in the Vercel dashboard under **Project Settings → Environment Variables**:

| Variable | Description | Example | Required |
|---|---|---|---|
| `SECRET_KEY` | Secret key for JWT signing and session security | `your-random-secret-key-min-32-chars` | Yes |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./booknest.db` | Yes |
| `ENVIRONMENT` | Deployment environment | `production` | Yes |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `https://your-app.vercel.app` | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry in minutes | `30` | No |
| `DEBUG` | Enable debug mode | `false` | No |

#### Setting Variables via CLI

```bash
vercel env add SECRET_KEY production
vercel env add DATABASE_URL production
vercel env add ENVIRONMENT production
vercel env add ALLOWED_ORIGINS production
```

#### Setting Variables via Dashboard

1. Go to your project on [vercel.com](https://vercel.com)
2. Navigate to **Settings** → **Environment Variables**
3. Add each variable for the appropriate environment (Production, Preview, Development)

---

### Database Considerations for Serverless

#### SQLite Limitations

SQLite is **not recommended** for production deployments on Vercel due to the following constraints:

- **Ephemeral filesystem:** Vercel serverless functions have a read-only filesystem (except `/tmp`). SQLite databases written to `/tmp` are lost between invocations.
- **No shared state:** Each serverless function instance has its own isolated filesystem. Concurrent requests may hit different instances with different database states.
- **Cold starts:** Database files in `/tmp` do not persist across cold starts.

#### Recommended Alternatives for Production

| Database | Connection String Format | Notes |
|---|---|---|
| **PostgreSQL (Vercel Postgres)** | `postgresql+asyncpg://user:pass@host:5432/dbname` | Native Vercel integration, recommended |
| **PostgreSQL (Neon)** | `postgresql+asyncpg://user:pass@host.neon.tech/dbname?sslmode=require` | Serverless-friendly, free tier available |
| **PostgreSQL (Supabase)** | `postgresql+asyncpg://user:pass@host.supabase.co:5432/dbname` | Generous free tier |
| **MySQL (PlanetScale)** | `mysql+aiomysql://user:pass@host/dbname?ssl=true` | Serverless-friendly |

#### Migrating from SQLite to PostgreSQL

1. Update `requirements.txt` — replace `aiosqlite` with `asyncpg`:
   ```
   asyncpg>=0.29.0
   ```

2. Update the `DATABASE_URL` environment variable:
   ```
   postgresql+asyncpg://username:password@hostname:5432/booknest
   ```

3. Ensure all SQLAlchemy models use database-agnostic types (avoid SQLite-specific syntax).

4. Run migrations against the new database before deploying.

#### Using SQLite for Local Development Only

For local development, SQLite with `aiosqlite` works well:

```
DATABASE_URL=sqlite+aiosqlite:///./booknest.db
```

Create a `.env` file in the project root (never commit this file):

```env
SECRET_KEY=local-dev-secret-key-change-in-production
DATABASE_URL=sqlite+aiosqlite:///./booknest.db
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
DEBUG=true
```

---

### Build Commands

#### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Vercel Deployment

```bash
# Login to Vercel
vercel login

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

Vercel automatically runs `pip install -r requirements.txt` during the build phase.

#### Custom Build Command (if needed)

If you need a custom build step (e.g., database table creation, static asset compilation), add a `build` script:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb"
      }
    }
  ]
}
```

---

### Database Initialization

The application uses SQLAlchemy's `create_all` within the FastAPI lifespan handler to create tables on startup. For serverless environments with external databases, tables are created on the first cold start.

For production deployments with PostgreSQL, consider using Alembic for migrations:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Generate a migration
alembic revision --autogenerate -m "initial"

# Apply migrations
alembic upgrade head
```

---

### CI/CD Notes

#### GitHub Integration

1. Connect your GitHub repository to Vercel via the dashboard
2. Vercel automatically deploys on every push:
   - **Push to `main`** → Production deployment
   - **Push to other branches** → Preview deployment
   - **Pull requests** → Preview deployment with unique URL

#### Running Tests Before Deployment

Add a GitHub Actions workflow at `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -v
        env:
          SECRET_KEY: test-secret-key-for-ci
          DATABASE_URL: sqlite+aiosqlite:///./test.db
          ENVIRONMENT: testing
          ALLOWED_ORIGINS: http://localhost:8000
```

#### Pre-deployment Checklist

- [ ] All tests pass locally (`pytest -v`)
- [ ] Environment variables are set in Vercel dashboard
- [ ] `SECRET_KEY` is a strong, unique value (not the development default)
- [ ] `DEBUG` is set to `false` in production
- [ ] `ALLOWED_ORIGINS` contains only your production domain(s)
- [ ] Database is accessible from Vercel's network (if using external DB)
- [ ] No SQLite `DATABASE_URL` in production environment variables

---

### Troubleshooting

#### Common Issues

| Issue | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError` | Missing dependency | Verify package is in `requirements.txt` |
| `500 Internal Server Error` | Unhandled exception | Check Vercel function logs in the dashboard |
| `ValidationError: extra fields not permitted` | Unexpected env vars injected by Vercel | Ensure Pydantic Settings uses `extra="ignore"` |
| Database connection timeout | Network/firewall issue | Whitelist Vercel IP ranges in your DB provider |
| `TemplateNotFound` | Wrong template directory path | Use absolute path with `Path(__file__).resolve()` |
| Cold start latency | Large dependency bundle | Minimize dependencies, increase `maxLambdaSize` if needed |

#### Viewing Logs

```bash
# View deployment logs
vercel logs <deployment-url>

# View real-time logs
vercel logs <deployment-url> --follow
```

#### Vercel Dashboard Logs

1. Go to your project on [vercel.com](https://vercel.com)
2. Click on a deployment
3. Navigate to **Functions** tab to see invocation logs
4. Navigate to **Runtime Logs** for real-time output

---

### Security Reminders

- **Never commit `.env` files** — add `.env` to `.gitignore`
- **Rotate `SECRET_KEY`** periodically and after any suspected compromise
- **Use HTTPS only** — Vercel provides this by default
- **Restrict CORS origins** — never use `*` in production
- **Keep dependencies updated** — run `pip audit` regularly to check for vulnerabilities