from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await auth_service.register(db, payload)
    return auth_service.build_token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await auth_service.login(db, payload)


@router.post("/google", response_model=TokenResponse)
async def google(payload: GoogleAuthRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await auth_service.google_auth(db, payload.code, payload.redirect_uri)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> TokenResponse:
    if await auth_service.is_refresh_token_blocklisted(redis_client, payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return await auth_service.refresh_token(db, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    redis_client: Redis = Depends(get_redis),
) -> Response:
    await auth_service.logout(redis_client, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
