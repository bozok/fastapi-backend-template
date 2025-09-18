"""
Test configuration and fixtures for FastAPI Clean Project.

This module provides async database fixtures, authentication helpers,
and test utilities for comprehensive testing of the FastAPI application.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator
import os

from app.main import app
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate
from app.crud.user import user as crud_user
from app.core.security import create_access_token
from app.api.deps import get_session


# Configure test database URL
TEST_DATABASE_URL = os.getenv("DATABASE_URL_TEST") or settings.DATABASE_URL_TEST


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session and tables for each test.
    This approach avoids event loop conflicts by keeping everything simple.
    """
    # Create a simple engine without pooling
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    try:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Create session
        async with AsyncSession(engine) as session:
            yield session

    finally:
        # Clean up tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

        # Dispose engine
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an HTTP client for testing FastAPI endpoints.
    Overrides the database dependency to use the test session.
    """

    def override_get_session():
        return db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client

    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for authentication tests."""
    user_data = UserCreate(
        email="testuser@example.com", full_name="Test User", password="testpassword123"
    )
    return await crud_user.create(db_session, obj_in=user_data)


@pytest_asyncio.fixture
async def test_inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive test user."""
    user_data = UserCreate(
        email="inactive@example.com",
        full_name="Inactive User",
        password="testpassword123",
    )
    user = await crud_user.create(db_session, obj_in=user_data)
    # Make the user inactive
    user.is_active = False
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_superuser(db_session: AsyncSession) -> User:
    """Create a superuser for admin tests."""
    user_data = UserCreate(
        email="admin@example.com", full_name="Admin User", password="adminpassword123"
    )
    user = await crud_user.create(db_session, obj_in=user_data)
    # Make the user a superuser
    user.is_superuser = True
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Create authentication headers for API tests."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(test_superuser: User) -> dict[str, str]:
    """Create admin authentication headers for API tests."""
    token = create_access_token(data={"sub": test_superuser.email})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def inactive_auth_headers(test_inactive_user: User) -> dict[str, str]:
    """Create authentication headers for inactive user tests."""
    token = create_access_token(data={"sub": test_inactive_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def invalid_auth_headers() -> dict[str, str]:
    """Create invalid authentication headers for testing auth failures."""
    return {"Authorization": "Bearer invalid.jwt.token"}


class TestUtils:
    """Utility class for common test assertions and helpers."""

    def assert_pagination_meta(self, pagination: dict, expected_total: int = None):
        """Assert that pagination metadata has the correct structure."""
        assert "current_page" in pagination
        assert "limit" in pagination
        assert "total_items" in pagination
        assert "total_pages" in pagination

        # Check types
        assert isinstance(pagination["current_page"], int)
        assert isinstance(pagination["limit"], int)
        assert isinstance(pagination["total_items"], int)
        assert isinstance(pagination["total_pages"], int)

        # Check values are positive
        assert pagination["current_page"] > 0
        assert pagination["limit"] > 0
        assert pagination["total_items"] >= 0
        assert pagination["total_pages"] >= 0

        # Check expected total if provided
        if expected_total is not None:
            assert pagination["total_items"] == expected_total


@pytest.fixture
def test_utils() -> TestUtils:
    """Provide test utility functions."""
    return TestUtils()


# Test data fixtures
@pytest.fixture
def user_create_data() -> dict:
    """Standard user creation data for tests."""
    return {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "testpassword123",
    }


@pytest.fixture
def user_update_data() -> dict:
    """Standard user update data for tests."""
    return {"full_name": "Updated User Name", "email": "updated@example.com"}
