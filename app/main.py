# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging, get_logger, audit
from app.core.rate_limit import limiter, custom_rate_limit_exceeded_handler
from app.middleware.logging import LoggingMiddleware, PerformanceLoggingMiddleware

# Import models to register them with SQLModel
from app.models import User  # noqa: F401

# Initialize logging system
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Note: Database tables are now managed by Alembic migrations.
    Run 'make migrate' to apply schema changes.
    """
    # Startup
    logger.info(
        "🚀 Starting FastAPI application",
        extra={
            "event_type": "system",
            "event_category": "startup",
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG,
        },
    )

    logger.info("📊 Database schema is managed by Alembic migrations")
    logger.info("💡 Run 'make migrate' to ensure database is up to date")

    # Log documentation status
    if settings.ENABLE_DOCS:
        logger.info("📚 API documentation is ENABLED")
        logger.info(f"   📖 Swagger UI: {settings.DOCS_URL}")
        logger.info(f"   📋 ReDoc: {settings.REDOC_URL}")
        logger.info(f"   🔧 OpenAPI: {settings.OPENAPI_URL}")
    else:
        logger.info("📚 API documentation is DISABLED for security")

    # Log pgAdmin status
    if settings.ENABLE_PGADMIN:
        logger.info("🔧 pgAdmin is ENABLED for database management")
        logger.info("   🌐 Access: http://localhost:5050 (if running)")
    else:
        logger.info("🔧 pgAdmin is DISABLED for security")

    # Log system configuration
    audit.log_security_event(
        "application_startup",
        f"FastAPI application started in {settings.ENVIRONMENT} mode",
        severity="info",
        details={
            "environment": settings.ENVIRONMENT,
            "debug_mode": settings.DEBUG,
            "logging_level": settings.LOG_LEVEL,
            "rate_limiting": settings.ENABLE_RATE_LIMITING,
            "api_docs": settings.ENABLE_DOCS,
            "pgadmin": settings.ENABLE_PGADMIN,
        },
    )

    yield

    # Shutdown
    logger.info(
        "🛑 Shutting down FastAPI application",
        extra={"event_type": "system", "event_category": "shutdown"},
    )

    audit.log_security_event(
        "application_shutdown",
        "FastAPI application shutdown completed",
        severity="info",
    )


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=settings.OPENAPI_URL if settings.ENABLE_DOCS else None,
    docs_url=settings.DOCS_URL if settings.ENABLE_DOCS else None,
    redoc_url=settings.REDOC_URL if settings.ENABLE_DOCS else None,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# --- Logging Middleware ---
# Build exclude paths list dynamically based on configuration
exclude_paths = [
    "/health",
    "/metrics",
    "/favicon.ico",
]

# Add documentation paths to exclude list only if docs are enabled
if settings.ENABLE_DOCS:
    exclude_paths.extend(["/docs", "/redoc", "/openapi.json"])

app.add_middleware(
    LoggingMiddleware,
    exclude_paths=exclude_paths,
    mask_query_params=["password", "token", "secret", "key", "auth"],
    mask_headers=["authorization", "cookie", "x-api-key", "x-auth-token"],
)

# Add performance monitoring if enabled
if settings.ENABLE_PERFORMANCE_LOGS:
    app.add_middleware(
        PerformanceLoggingMiddleware, slow_threshold=settings.SLOW_REQUEST_THRESHOLD
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

    logger.info(
        "CORS middleware configured",
        extra={"event_type": "system", "allowed_origins": cors_origins},
    )


# --- Routers v1 ---
app.include_router(api_router, prefix=settings.API_STR)

logger.info(
    "API routes configured",
    extra={"event_type": "system", "api_prefix": settings.API_STR},
)


# Enhanced health check with logging
@app.get("/health", tags=["Health Check"])
async def health_check():
    """Enhanced health check endpoint with logging"""
    logger.info(
        "Health check requested",
        extra={"event_type": "health_check", "status": "healthy"},
    )

    return {
        "message": f"Welcome to {settings.PROJECT_NAME}!",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",  # You can make this dynamic
    }
