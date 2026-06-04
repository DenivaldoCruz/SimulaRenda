from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nicegui import ui
from redis.asyncio import Redis
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.routes import auth, simulations, users
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import engine
from app.ui import register_pages


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await engine.dispose()


app = FastAPI(title="SimulaRenda API", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(simulations.router, prefix="/api/v1", tags=["simulations"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Retorna o status básico da aplicação."""
    return {"status": "healthy"}


register_pages()

ui.run_with(
    app,
    mount_path="/",
    storage_secret=settings.nicegui_storage_secret,
    title="SimulaRenda",
    favicon="💰",
    dark=False,
)
