# BookNest

A modern book management API built with Python 3.11+ and FastAPI.

## Features

- **Book Management** — Create, read, update, and delete books
- **User Authentication** — JWT-based authentication with secure password hashing
- **Search & Filtering** — Search books by title, author, genre, and more
- **Collections** — Organize books into personal collections
- **Reviews & Ratings** — Rate and review books
- **Async Architecture** — Fully asynchronous with SQLAlchemy 2.0 and aiosqlite
- **Input Validation** — Pydantic v2 schemas for all request/response models
- **CORS Support** — Configurable cross-origin resource sharing

## Tech Stack

- **Runtime:** Python 3.11+
- **Framework:** FastAPI
- **Database:** SQLite (async via aiosqlite) / PostgreSQL (via asyncpg)
- **ORM:** SQLAlchemy 2.0 (async)
- **Auth:** JWT (python-jose) + bcrypt password hashing
- **Validation:** Pydantic v2
- **Server:** Uvicorn (ASGI)
- **Testing:** pytest + pytest-asyncio + httpx

## Folder Structure

```
booknest/
├── app/
│   ├── core/
│   │   ├── config.py          # Application settings (BaseSettings)
│   │   ├── database.py        # Async engine, session factory, Base
│   │   ├── security.py        # JWT token creation/verification, password hashing
│   │   └── __init__.py
│   ├── models/
│   │   ├── user.py            # User model
│   │   ├── book.py            # Book model
│   │   ├── collection.py      # Collection model
│   │   ├── review.py          # Review model
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── user.py            # User request/response schemas
│   │   ├── book.py            # Book request/response schemas
│   │   ├── collection.py      # Collection schemas
│   │   ├── review.py          # Review schemas
│   │   └── __init__.py
│   ├── services/
│   │   ├── user.py            # User business logic
│   │   ├── book.py            # Book business logic
│   │   ├── collection.py      # Collection business logic
│   │   ├── review.py          # Review business logic
│   │   └── __init__.py
│   ├── routers/
│   │   ├── auth.py            # Authentication routes
│   │   ├── users.py           # User routes
│   │   ├── books.py           # Book routes
│   │   ├── collections.py     # Collection routes
│   │   ├── reviews.py         # Review routes
│   │   └── __init__.py
│   ├── dependencies/
│   │   ├── auth.py            # Auth dependency (get_current_user)
│   │   └── __init__.py
│   ├── main.py                # FastAPI app entry point
│   └── __init__.py
├── tests/
│   ├── test_auth.py
│   ├── test_books.py
│   ├── test_collections.py
│   ├── test_reviews.py
│   └── conftest.py
├── .env                       # Environment variables (not committed)
├── .env.example               # Example environment variables
├── requirements.txt           # Python dependencies
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd booknest
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and update values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
DATABASE_URL=sqlite+aiosqlite:///./booknest.db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 5. Initialize the Database

The database tables are created automatically on first startup via the lifespan handler. To seed initial data:

```bash
python -m app.seed
```

### 6. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## Environment Variables

| Variable                     | Description                          | Default                                |
|------------------------------|--------------------------------------|----------------------------------------|
| `DATABASE_URL`               | Async database connection string     | `sqlite+aiosqlite:///./booknest.db`    |
| `SECRET_KEY`                 | JWT signing secret                   | *(required)*                           |
| `ALGORITHM`                  | JWT algorithm                        | `HS256`                                |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| Token expiration in minutes          | `30`                                   |
| `CORS_ORIGINS`               | Comma-separated allowed origins      | `http://localhost:3000`                |

## API Endpoints

### Authentication

| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| POST   | `/auth/register`   | Register a new user      |
| POST   | `/auth/login`      | Login and receive JWT    |

### Users

| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| GET    | `/users/me`        | Get current user profile |
| PUT    | `/users/me`        | Update current user      |

### Books

| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| GET    | `/books`           | List all books (paginated, filterable) |
| POST   | `/books`           | Create a new book        |
| GET    | `/books/{id}`      | Get book details         |
| PUT    | `/books/{id}`      | Update a book            |
| DELETE | `/books/{id}`      | Delete a book            |

### Collections

| Method | Endpoint                        | Description                    |
|--------|---------------------------------|--------------------------------|
| GET    | `/collections`                  | List user's collections        |
| POST   | `/collections`                  | Create a new collection        |
| GET    | `/collections/{id}`             | Get collection details         |
| PUT    | `/collections/{id}`             | Update a collection            |
| DELETE | `/collections/{id}`             | Delete a collection            |
| POST   | `/collections/{id}/books/{book_id}` | Add book to collection    |
| DELETE | `/collections/{id}/books/{book_id}` | Remove book from collection |

### Reviews

| Method | Endpoint                  | Description              |
|--------|---------------------------|--------------------------|
| GET    | `/books/{book_id}/reviews`| List reviews for a book  |
| POST   | `/books/{book_id}/reviews`| Create a review          |
| PUT    | `/reviews/{id}`           | Update a review          |
| DELETE | `/reviews/{id}`           | Delete a review          |

## Interactive API Documentation

FastAPI provides auto-generated interactive documentation:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Running Tests

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Deployment to Vercel

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Create `vercel.json`

```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

### 3. Set Environment Variables

Configure all required environment variables in the Vercel dashboard under **Settings → Environment Variables**. Use a PostgreSQL connection string for `DATABASE_URL` in production:

```
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/booknest
```

### 4. Deploy

```bash
vercel --prod
```

## Development

### Code Style

- Follow PEP 8 conventions
- Use type hints for all function parameters and return values
- Use `async def` for all I/O-bound operations
- Use structured logging via Python's `logging` module

### Adding a New Resource

1. Create the SQLAlchemy model in `app/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Create service functions in `app/services/`
4. Create router endpoints in `app/routers/`
5. Register the router in `app/main.py`
6. Update `__init__.py` files to re-export new symbols
7. Write tests in `tests/`

## License

Private — All rights reserved.