# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.rate_limit import limiter, custom_rate_limit_exceeded_handler

# Import models to register them with SQLModel
from app.models import User  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Note: Database tables are now managed by Alembic migrations.
    Run 'make migrate' to apply schema changes.
    """
    # Startup
    print("🚀 Starting FastAPI application...")
    print("📊 Database schema is managed by Alembic migrations")
    print("💡 Run 'make migrate' to ensure database is up to date")

    yield

    # Shutdown
    print("🛑 Shutting down FastAPI application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=settings.OPENAPI_URL,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# --- Rate Limiting Setup ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

# --- CORS ---
# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    # Convert AnyHttpUrl objects to strings and remove trailing slashes
    cors_origins = [str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# --- Routers v1 ---
app.include_router(api_router, prefix=settings.API_STR)


# Basic root endpoint / health check
@app.get("/health", tags=["Health Check"])
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}
