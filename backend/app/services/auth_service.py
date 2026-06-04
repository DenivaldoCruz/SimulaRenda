from datetime import timedelta
from typing import Protocol
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
REFRESH_TOKEN_BLOCKLIST_PREFIX = "auth:refresh_blocklist:"


class RedisBlocklistClient(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def setex(self, key: str, time: timedelta, value: str) -> object: ...


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    normalized_email = email.strip().lower()
    result = await db.execute(
        select(User).where(User.email == normalized_email, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


def _token_response_for(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=user,
    )


async def _get_active_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    user = await db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    return user


async def register(db: AsyncSession, data: RegisterRequest) -> User:
    normalized_email = str(data.email).strip().lower()
    if await get_user_by_email(db, normalized_email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )

    user = User(
        email=normalized_email,
        name=data.name.strip() if data.name else None,
        birth_date=data.birth_date,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        ) from exc
    await db.refresh(user)
    return user


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    user = await get_user_by_email(db, str(data.email))
    if user is None or user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )
    return _token_response_for(user)


async def google_auth(db: AsyncSession, code: str, redirect_uri: str) -> TokenResponse:
    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID or "",
                "client_secret": settings.GOOGLE_CLIENT_SECRET or "",
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Falha na autenticação Google",
            )
        token_payload = token_response.json()
        google_access_token = token_payload.get("access_token")
        if not google_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Falha na autenticação Google",
            )

        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )
        if userinfo_response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Falha na autenticação Google",
            )
        userinfo = userinfo_response.json()

    email = str(userinfo.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Conta Google sem e-mail válido",
        )

    user = await get_user_by_email(db, email)
    if user is None:
        user = User(
            email=email,
            name=str(userinfo.get("name") or "").strip() or None,
            hashed_password=None,
        )
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            user = await get_user_by_email(db, email)
            if user is None:
                raise
        else:
            await db.refresh(user)

    return _token_response_for(user)


async def refresh_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token)
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    try:
        user_id = UUID(str(payload.get("sub")))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        ) from None
    user = await _get_active_user_by_id(db, user_id)
    return _token_response_for(user)


async def is_refresh_token_blocklisted(
    redis_client: RedisBlocklistClient, refresh_token: str
) -> bool:
    value = await redis_client.get(f"{REFRESH_TOKEN_BLOCKLIST_PREFIX}{refresh_token}")
    return value is not None


async def logout(redis_client: RedisBlocklistClient, refresh_token: str) -> None:
    # Validate first so malformed/expired values cannot pollute the blocklist.
    payload = decode_token(refresh_token)
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    await redis_client.setex(
        f"{REFRESH_TOKEN_BLOCKLIST_PREFIX}{refresh_token}",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "1",
    )


# Backward-compatible helpers used by older code paths.
async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if user is None or user.hashed_password is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(db: AsyncSession, payload: RegisterRequest) -> User:
    return await register(db, payload)


def build_token_response(user: User) -> TokenResponse:
    return _token_response_for(user)
