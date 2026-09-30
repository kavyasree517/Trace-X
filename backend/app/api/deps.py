"""FastAPI dependencies for request handling, authentication, and database sessions."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings

_engine = None
_session_maker = None


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    global _engine, _session_maker
    if _session_maker is None:
        settings = get_settings()
        _engine = create_async_engine(settings.DATABASE_URL, echo=False)
        _session_maker = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    return _session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an asynchronous database session."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        yield session


def require_investigator_token(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
) -> str:
    """Verify investigator bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed authorization header",
        )
    token = authorization.split("Bearer ", 1)[1].strip()
    if token != settings.INVESTIGATOR_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid investigator credentials",
        )
    return token


def require_admin_token(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
) -> str:
    """Verify administrator bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed authorization header",
        )
    token = authorization.split("Bearer ", 1)[1].strip()
    if token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid administrator credentials",
        )
    return token
