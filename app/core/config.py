from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "My FastAPI App"
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/dbname"
    # Security settings
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    SECRET_KEY: str = "super-secret-key-placeholder"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Frontend URL for password reset emails
    FRONTEND_URL: str = "http://localhost:3000"

    DEBUG: bool = True
    API_STR: str = "/api/v1"

    # Environment settings
    ENVIRONMENT: str = "development"  # development, staging, production

    # Documentation settings - disable in production
    ENABLE_DOCS: bool = True

    ENABLE_RATE_LIMITING: bool = False

    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: str = "password"

    # OpenAPI settings
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    # Logging settings
    LOG_LEVEL: str = "INFO"
    ENABLE_JSON_LOGS: bool = False  # Set to True in production
    ENABLE_AUDIT_LOGS: bool = True
    ENABLE_PERFORMANCE_LOGS: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    SLOW_REQUEST_THRESHOLD: float = 1.0  # seconds

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
