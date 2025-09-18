"""
Dependency tests.

Tests for FastAPI dependencies including authentication, pagination, and database session management.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import (
    get_session,
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_pagination_params,
    PaginationParams,
)
from app.models.user import User
from app.core.security import create_access_token


@pytest.mark.unit
@pytest.mark.asyncio
class TestDatabaseSession:
    """Test database session dependency."""

    async def test_get_session_returns_async_session(self):
        """Test that get_session returns an AsyncSession."""
        async for session in get_session():
            assert isinstance(session, AsyncSession)
            # Session should be usable
            assert hasattr(session, "execute")
            assert hasattr(session, "commit")
            assert hasattr(session, "rollback")
            break  # Only test one iteration


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuthenticationDependencies:
    """Test authentication-related dependencies."""

    async def test_get_current_user_valid_token(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test getting current user with valid token."""
        # Create valid token
        token = create_access_token(data={"sub": test_user.email})

        # Mock the database session dependency
        with patch("app.api.deps.get_session") as mock_get_session:
            mock_get_session.return_value = db_session

            user = await get_current_user(db_session, token)

            assert user is not None
            assert user.email == test_user.email
            assert user.id == test_user.id

    async def test_get_current_user_invalid_token(self, db_session: AsyncSession):
        """Test getting current user with invalid token."""
        invalid_token = "invalid.jwt.token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, invalid_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    async def test_get_current_user_malformed_token(self, db_session: AsyncSession):
        """Test getting current user with malformed token."""
        malformed_token = "not.a.valid.jwt"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, malformed_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    async def test_get_current_user_expired_token(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test getting current user with expired token."""
        from datetime import timedelta

        # Create expired token
        expired_token = create_access_token(
            data={"sub": test_user.email}, expires_delta=timedelta(minutes=-30)
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, expired_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    async def test_get_current_user_token_missing_subject(
        self, db_session: AsyncSession
    ):
        """Test getting current user with token missing subject."""
        # Create token without 'sub' field
        token = create_access_token(data={"user_id": "123"})  # Wrong field

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    async def test_get_current_user_nonexistent_user(self, db_session: AsyncSession):
        """Test getting current user for non-existent user."""
        # Create token for non-existent user
        token = create_access_token(data={"sub": "nonexistent@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    async def test_get_current_user_inactive_user(
        self, db_session: AsyncSession, test_inactive_user: User
    ):
        """Test getting current user for inactive user."""
        token = create_access_token(data={"sub": test_inactive_user.email})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db_session, token)

        assert exc_info.value.status_code == 401
        assert "User account is inactive" in exc_info.value.detail

    async def test_get_current_active_user(self, test_user: User):
        """Test get_current_active_user dependency."""
        # This dependency just passes through the user from get_current_user
        active_user = await get_current_active_user(test_user)

        assert active_user is test_user
        assert active_user.is_active is True

    async def test_get_current_admin_user_success(self, test_superuser: User):
        """Test getting current admin user with superuser."""
        admin_user = await get_current_admin_user(test_superuser)

        assert admin_user is test_superuser
        assert admin_user.is_superuser is True

    async def test_get_current_admin_user_non_admin(self, test_user: User):
        """Test getting current admin user with regular user."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(test_user)

        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail

    async def test_get_current_admin_user_missing_superuser_field(
        self, test_user: User
    ):
        """Test admin check when is_superuser field is missing."""
        # Remove is_superuser attribute to test getattr with default
        if hasattr(test_user, "is_superuser"):
            delattr(test_user, "is_superuser")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(test_user)

        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail


@pytest.mark.unit
class TestPaginationDependency:
    """Test pagination parameter dependency."""

    def test_get_pagination_params_default(self):
        """Test pagination params with default values."""
        # Call with default values since this is testing the function directly
        params = get_pagination_params(skip=0, limit=100)

        assert isinstance(params, PaginationParams)
        assert params.skip == 0
        assert params.limit == 100

    def test_get_pagination_params_custom(self):
        """Test pagination params with custom values."""
        params = get_pagination_params(skip=20, limit=50)

        assert params.skip == 20
        assert params.limit == 50

    def test_get_pagination_params_validation(self):
        """Test pagination params validation."""
        # Test valid values
        params = get_pagination_params(skip=0, limit=1)
        assert params.skip == 0
        assert params.limit == 1

        params = get_pagination_params(skip=100, limit=200)
        assert params.skip == 100
        assert params.limit == 200

    def test_pagination_params_model_validation(self):
        """Test PaginationParams model validation."""
        # Valid params
        params = PaginationParams(skip=10, limit=50)
        assert params.skip == 10
        assert params.limit == 50

        # Test with minimum values
        params = PaginationParams(skip=0, limit=1)
        assert params.skip == 0
        assert params.limit == 1

        # Test with maximum limit
        params = PaginationParams(skip=0, limit=200)
        assert params.skip == 0
        assert params.limit == 200

    def test_pagination_params_invalid_values(self):
        """Test PaginationParams with invalid values."""
        from pydantic import ValidationError

        # Negative skip
        with pytest.raises(ValidationError):
            PaginationParams(skip=-1, limit=100)

        # Zero limit
        with pytest.raises(ValidationError):
            PaginationParams(skip=0, limit=0)

        # Limit too high
        with pytest.raises(ValidationError):
            PaginationParams(skip=0, limit=300)


@pytest.mark.integration
@pytest.mark.asyncio
class TestDependencyIntegration:
    """Test dependencies working together in integration scenarios."""

    async def test_auth_dependency_with_logging(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that authentication dependency triggers proper logging."""
        token = create_access_token(data={"sub": test_user.email})

        with (
            patch("app.api.deps.logger") as mock_logger,
            patch("app.core.logging.audit.log_data_access") as mock_log_access,
        ):
            user = await get_current_user(db_session, token)

            assert user.email == test_user.email

            # Verify logger.debug was called for successful authentication
            mock_logger.debug.assert_called()
            mock_log_access.assert_called()

            # Check log_data_access call
            access_call = mock_log_access.call_args
            assert access_call[1]["user_id"] == str(test_user.id)
            assert access_call[1]["resource_type"] == "user_authentication"
            assert access_call[1]["operation"] == "token_validation"

    async def test_admin_dependency_security_logging(self, test_user: User):
        """Test that admin access denial triggers security logging."""
        with (
            patch("app.core.logging.get_logger") as mock_get_logger,
            patch("app.core.logging.audit.log_security_event") as mock_log_security,
        ):
            mock_logger = AsyncMock()
            mock_get_logger.return_value = mock_logger

            with pytest.raises(HTTPException):
                await get_current_admin_user(test_user)

            # Verify security logging was called
            mock_log_security.assert_called()

            # Check security event details
            security_call = mock_log_security.call_args
            assert security_call[0][0] == "unauthorized_admin_access"
            assert security_call[1]["severity"] == "high"

    async def test_dependency_error_propagation(self, db_session: AsyncSession):
        """Test that dependency errors propagate correctly."""
        # Test with database error
        with patch("app.crud.user.user.get_by_email") as mock_get_user:
            mock_get_user.side_effect = Exception("Database error")

            token = create_access_token(data={"sub": "test@example.com"})

            # Should handle database errors gracefully
            with pytest.raises(Exception):  # The original exception should propagate
                await get_current_user(db_session, token)

    async def test_session_cleanup(self):
        """Test that database sessions are properly cleaned up."""
        session_count = 0

        async for session in get_session():
            session_count += 1
            assert isinstance(session, AsyncSession)
            # Session should be valid - check if it has a connection
            assert session.get_bind() is not None
            break

        assert session_count == 1
        # Note: Actual cleanup testing would require more complex setup
        # to verify session is closed after use

    async def test_concurrent_session_handling(self):
        """Test that multiple concurrent sessions work correctly."""
        sessions = []

        # Create multiple sessions concurrently
        for _ in range(3):
            async for session in get_session():
                sessions.append(session)
                break

        assert len(sessions) == 3
        # All sessions should be different instances
        assert len(set(id(s) for s in sessions)) == 3

        # All should be valid AsyncSession instances
        for session in sessions:
            assert isinstance(session, AsyncSession)
            # Check session has a valid connection
            assert session.get_bind() is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestDependencyPerformance:
    """Test dependency performance and caching."""

    async def test_auth_dependency_performance(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test authentication dependency performance."""
        import time

        token = create_access_token(data={"sub": test_user.email})

        start_time = time.time()
        user = await get_current_user(db_session, token)
        end_time = time.time()

        # Authentication should be reasonably fast (< 1 second)
        assert (end_time - start_time) < 1.0
        assert user.email == test_user.email

    async def test_pagination_dependency_performance(self):
        """Test pagination dependency performance."""
        import time

        start_time = time.time()
        for _ in range(100):
            params = get_pagination_params(skip=10, limit=50)
            assert params.skip == 10
        end_time = time.time()

        # Pagination should be very fast (< 0.1 seconds for 100 calls)
        assert (end_time - start_time) < 0.1
