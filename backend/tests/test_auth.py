from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient
from jose import jwt

from app.api.v1.routes.auth import get_redis
from app.core.config import settings
from app.core.security import ALGORITHM, REFRESH_TOKEN_TYPE
from app.main import app
from app.services.auth_service import GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def setex(self, key: str, _ttl: object, value: str) -> None:
        self.values[key] = value


@pytest.fixture
async def fake_redis() -> FakeRedis:
    redis = FakeRedis()
    app.dependency_overrides[get_redis] = lambda: redis
    return redis


async def test_register_duplicate_email_returns_409(
    async_client: AsyncClient,
    fake_redis: FakeRedis,
) -> None:
    payload = {
        "email": "ana@example.com",
        "name": "Ana",
        "password": "strong-password",
    }

    first_response = await async_client.post("/api/v1/auth/register", json=payload)
    second_response = await async_client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_409_CONFLICT


async def test_login_wrong_password_returns_401(
    async_client: AsyncClient,
    fake_redis: FakeRedis,
) -> None:
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "bruno@example.com", "password": "correct-password"},
    )

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "bruno@example.com", "password": "wrong-password"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_expired_refresh_token_returns_401(
    async_client: AsyncClient,
    fake_redis: FakeRedis,
) -> None:
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "carla@example.com", "password": "safe-password"},
    )
    user_id = register_response.json()["user"]["id"]
    expired_token = jwt.encode(
        {
            "sub": user_id,
            "type": REFRESH_TOKEN_TYPE,
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_token},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_logout_invalidates_refresh_token(
    async_client: AsyncClient,
    fake_redis: FakeRedis,
) -> None:
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "diego@example.com", "password": "safe-password"},
    )
    refresh_token = register_response.json()["refresh_token"]

    first_refresh_response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    logout_response = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    second_refresh_response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert first_refresh_response.status_code == status.HTTP_200_OK
    assert logout_response.status_code == status.HTTP_204_NO_CONTENT
    assert second_refresh_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_google_oauth_mocked_with_httpx_mock(
    async_client: AsyncClient,
    fake_redis: FakeRedis,
    httpx_mock: object,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=GOOGLE_TOKEN_URL,
        json={"access_token": "google-access-token"},
    )
    httpx_mock.add_response(
        method="GET",
        url=GOOGLE_USERINFO_URL,
        json={"email": "eva@example.com", "name": "Eva"},
    )

    response = await async_client.post(
        "/api/v1/auth/google",
        json={"code": "oauth-code", "redirect_uri": "http://testserver/callback"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == "eva@example.com"
