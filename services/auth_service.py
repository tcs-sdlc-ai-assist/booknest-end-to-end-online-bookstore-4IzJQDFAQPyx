import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from utils.security import create_access_token, hash_password, verify_password


async def register_user(
    db: AsyncSession,
    display_name: str,
    email: str,
    username: str,
    password: str,
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    existing_email = result.scalars().first()
    if existing_email is not None:
        raise ValueError("Email already exists.")

    result = await db.execute(select(User).where(User.username == username))
    existing_username = result.scalars().first()
    if existing_username is not None:
        raise ValueError("Username already exists.")

    password_hash = hash_password(password)

    user = User(
        display_name=display_name,
        email=email,
        username=username,
        password_hash=password_hash,
        role="customer",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_jwt(user: User, expires_delta: Optional[timedelta] = None) -> str:
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
    }
    token = create_access_token(data=token_data, expires_delta=expires_delta)
    return token