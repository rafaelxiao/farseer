"""Auth API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from farseer.database import async_session_factory
from farseer.models.user import User
from farseer.services.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_user,
    decode_token,
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Dependency
async def get_db():
    async with async_session_factory() as db:
        yield db


async def get_current_user_dep(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await get_current_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return user


async def get_admin_user(user: User = Depends(get_current_user_dep)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# Schemas
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    is_admin: bool


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    is_approved: bool
    created_at: str

    class Config:
        from_attributes = True


# Endpoints
@router.post("/register", response_model=dict)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user (requires admin approval)."""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Check if email exists
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await create_user(db, req.username, req.email, req.password)
    return {"message": "Registration successful. Waiting for admin approval.", "user_id": user.id}


@router.post("/login", response_model=LoginResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login and get access token."""
    user = await authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Account pending approval")

    token = create_access_token({"sub": user.username})
    return LoginResponse(
        access_token=token,
        username=user.username,
        is_admin=user.is_admin,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user_dep)):
    """Get current user info."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_admin=user.is_admin,
        is_approved=user.is_approved,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """List all users (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            is_active=u.is_active,
            is_admin=u.is_admin,
            is_approved=u.is_approved,
            created_at=u.created_at.isoformat() if u.created_at else "",
        )
        for u in users
    ]


@router.put("/users/{user_id}/approve")
async def approve_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_approved = True
    await db.commit()
    return {"message": f"User {user.username} approved"}


@router.put("/users/{user_id}/reject")
async def reject_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_approved = False
    user.is_active = False
    await db.commit()
    return {"message": f"User {user.username} rejected"}


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle user active status (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    await db.commit()
    return {"message": f"User {user.username} {'activated' if user.is_active else 'deactivated'}"}
