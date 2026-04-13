import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from database import create_tables, SessionLocal
from models.user import User
from routers import auth, books, cart, checkout, orders, admin, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()

    async with SessionLocal() as db:
        try:
            result = await db.execute(select(User).limit(1))
            user = result.scalars().first()
            if user is None:
                from seed import seed
                await seed()
        except Exception:
            pass

    yield


app = FastAPI(
    title="BookNest",
    description="A modern book management API built with FastAPI",
    version="1.0.0",
    lifespan=lifespan,
)

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(profile.router)


@app.get("/")
async def root(request: Request):
    return RedirectResponse(url="/books", status_code=302)


@app.get("/healthz")
async def health_check():
    return {"status": "ok"}