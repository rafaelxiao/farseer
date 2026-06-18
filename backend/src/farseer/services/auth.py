"""Authentication service."""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.models.user import User

# Security
SECRET_KEY = os.getenv("JWT_SECRET", "farseer-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(db: AsyncSession, username: str, email: str, password: str) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_approved=False,  # Requires admin approval
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(db: AsyncSession, token: str) -> Optional[User]:
    payload = decode_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


# Initialize admin user
async def init_admin(db: AsyncSession):
    """Create admin user if not exists."""
    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if not admin:
        admin = User(
            username="admin",
            email="admin@farseer.local",
            hashed_password=get_password_hash("1qazxsw2"),
            is_active=True,
            is_admin=True,
            is_approved=True,
        )
        db.add(admin)
        await db.commit()
        print("Admin user created: admin / 1qazxsw2")
