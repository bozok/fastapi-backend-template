"""
User service layer tests.

Tests for user business logic, validation, and service operations.
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException
from pydantic_core import ValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.user import user_service
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserService:
    """Test user service business logic."""

    async def test_create_user_success(
        self, db_session: AsyncSession, user_create_data: dict
    ):
        """Test successful user creation with all validations."""
        user_data = UserCreate(**user_create_data)

        created_user = await user_service.create_user(db_session, user_in=user_data)

        assert created_user.email == user_data.email
        assert created_user.full_name == user_data.full_name
        assert created_user.is_active is True
        assert created_user.is_superuser is False
        assert created_user.hashed_password != user_data.password  # Should be hashed

    async def test_create_user_duplicate_email(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test user creation with duplicate email fails."""
        user_data = UserCreate(
            email=test_user.email,  # Duplicate email
            full_name="Another User",
            password="password123",
        )

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(db_session, user_in=user_data)

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

    async def test_create_user_empty_email(self, db_session: AsyncSession):
        """Test user creation with empty email fails at schema validation level."""
        # This should fail at Pydantic schema validation level
        with pytest.raises(ValidationError):
            UserCreate(email="", full_name="Test User", password="password123")

    async def test_create_user_whitespace_email(self, db_session: AsyncSession):
        """Test user creation with whitespace-only email fails at schema validation level."""
        # This should fail at Pydantic schema validation level
        with pytest.raises(ValidationError):
            UserCreate(email="   ", full_name="Test User", password="password123")

    async def test_create_user_empty_full_name(self, db_session: AsyncSession):
        """Test user creation with empty full name fails."""
        user_data = UserCreate(
            email="test@example.com", full_name="", password="password123"
        )

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(db_session, user_in=user_data)

        assert exc_info.value.status_code == 400
        assert "Full name is required" in exc_info.value.detail

    async def test_create_user_whitespace_full_name(self, db_session: AsyncSession):
        """Test user creation with whitespace-only full name fails."""
        user_data = UserCreate(
            email="test@example.com", full_name="   ", password="password123"
        )

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(db_session, user_in=user_data)

        assert exc_info.value.status_code == 400
        assert "Full name is required" in exc_info.value.detail

    async def test_create_user_empty_password(self, db_session: AsyncSession):
        """Test user creation with empty password fails."""
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password=""
        )

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(db_session, user_in=user_data)

        assert exc_info.value.status_code == 400
        assert "Password is required" in exc_info.value.detail

    async def test_create_user_whitespace_password(self, db_session: AsyncSession):
        """Test user creation with whitespace-only password fails."""
        user_data = UserCreate(
            email="test@example.com", full_name="Test User", password="   "
        )

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(db_session, user_in=user_data)

        assert exc_info.value.status_code == 400
        assert "Password is required" in exc_info.value.detail

    async def test_create_user_trims_whitespace(self, db_session: AsyncSession):
        """Test that user creation trims whitespace from email and full_name."""
        user_data = UserCreate(
            email="  test@example.com  ",
            full_name="  Test User  ",
            password="password123",
        )

        created_user = await user_service.create_user(db_session, user_in=user_data)

        assert created_user.email == "test@example.com"  # Trimmed
        assert created_user.full_name == "Test User"  # Trimmed

    @patch("app.services.user.hash_password")
    async def test_create_user_password_hashing_failure(
        self, mock_hash_password, db_session: AsyncSession, user_create_data: dict
    ):
        """Test user creation when password hashing fails."""
        mock_hash_password.side_effect = Exception("Hashing failed")
        user_data = UserCreate(**user_create_data)

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(db_session, user_in=user_data)

        assert exc_info.value.status_code == 500
        assert "Failed to hash password" in exc_info.value.detail

    @patch("app.crud.user.user.create")
    async def test_create_user_database_failure(
        self, mock_create, db_session: AsyncSession, user_create_data: dict
    ):
        """Test user creation when database operation fails."""
        mock_create.side_effect = Exception("Database error")
        user_data = UserCreate(**user_create_data)

        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(db_session, user_in=user_data)

        assert exc_info.value.status_code == 500
        assert "Failed to create user" in exc_info.value.detail

    async def test_update_user_success(self, db_session: AsyncSession, test_user: User):
        """Test successful user update."""
        update_data = UserUpdate(full_name="Updated Name", email="updated@example.com")

        updated_user = await user_service.update_user(
            db_session,
            user_id=str(test_user.id),
            user_in=update_data,
            current_user=test_user,
        )

        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == "updated@example.com"

    async def test_update_nonexistent_user(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating a non-existent user fails."""
        import uuid

        fake_id = str(uuid.uuid4())
        update_data = UserUpdate(full_name="Updated Name")

        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_user(
                db_session, user_id=fake_id, user_in=update_data, current_user=test_user
            )

        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    async def test_get_user_profile_success(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test successful user profile retrieval."""
        profile = await user_service.get_user_profile(
            db_session, user_id=str(test_user.id), requesting_user=test_user
        )

        assert profile.id == test_user.id
        assert profile.email == test_user.email
        assert profile.full_name == test_user.full_name

    async def test_get_nonexistent_user_profile(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test getting profile for non-existent user fails."""
        import uuid

        fake_id = str(uuid.uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_user_profile(
                db_session, user_id=fake_id, requesting_user=test_user
            )

        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserServiceIntegration:
    """Test user service integration with logging and audit."""

    @patch("app.core.logging.audit.log_security_event")
    @patch("app.core.logging.audit.log_user_action")
    async def test_create_user_audit_logging(
        self,
        mock_log_user_action,
        mock_log_security_event,
        db_session: AsyncSession,
        user_create_data: dict,
    ):
        """Test that user creation triggers proper audit logging."""
        user_data = UserCreate(**user_create_data)

        created_user = await user_service.create_user(db_session, user_in=user_data)

        # Verify audit logs were called
        mock_log_user_action.assert_called()
        mock_log_security_event.assert_called()

        # Check the log_user_action call
        user_action_call = mock_log_user_action.call_args
        assert user_action_call[1]["user_id"] == str(created_user.id)
        assert user_action_call[1]["action"] == "user_registration"

        # Check the log_security_event call
        security_event_call = mock_log_security_event.call_args
        assert security_event_call[0][0] == "user_registration"
        assert security_event_call[1]["severity"] == "info"

    @patch("app.core.logging.audit.log_security_event")
    async def test_create_user_duplicate_email_audit(
        self, mock_log_security_event, db_session: AsyncSession, test_user: User
    ):
        """Test that duplicate email attempts trigger security logging."""
        user_data = UserCreate(
            email=test_user.email, full_name="Another User", password="password123"
        )

        with pytest.raises(HTTPException):
            await user_service.create_user(db_session, user_in=user_data)

        # Verify security event was logged
        mock_log_security_event.assert_called()
        security_event_call = mock_log_security_event.call_args
        assert security_event_call[0][0] == "duplicate_user_registration"
        assert security_event_call[1]["severity"] == "low"

    @patch("app.core.logging.audit.log_user_action")
    async def test_update_user_audit_logging(
        self, mock_log_user_action, db_session: AsyncSession, test_user: User
    ):
        """Test that user updates trigger proper audit logging."""
        update_data = UserUpdate(full_name="Updated Name")

        await user_service.update_user(
            db_session,
            user_id=str(test_user.id),
            user_in=update_data,
            current_user=test_user,
        )

        # Verify audit log was called
        mock_log_user_action.assert_called()
        user_action_call = mock_log_user_action.call_args
        assert user_action_call[1]["user_id"] == str(test_user.id)
        assert user_action_call[1]["action"] == "user_update"

    @patch("app.core.logging.audit.log_data_access")
    async def test_get_user_profile_audit_logging(
        self, mock_log_data_access, db_session: AsyncSession, test_user: User
    ):
        """Test that profile access triggers data access logging."""
        await user_service.get_user_profile(
            db_session, user_id=str(test_user.id), requesting_user=test_user
        )

        # Verify data access was logged
        mock_log_data_access.assert_called()
        data_access_call = mock_log_data_access.call_args
        assert data_access_call[1]["user_id"] == str(test_user.id)
        assert data_access_call[1]["resource_type"] == "user_profile"
        assert data_access_call[1]["operation"] == "read"

    @patch("app.services.user.logger")
    async def test_service_performance_logging(
        self, mock_logger, db_session: AsyncSession, user_create_data: dict
    ):
        """Test that service operations trigger performance logging."""
        user_data = UserCreate(**user_create_data)

        # The @log_performance decorator should log performance metrics
        await user_service.create_user(db_session, user_in=user_data)

        # Verify logger was called (since the service has multiple log calls)
        assert mock_logger.info.called

    async def test_user_service_error_handling(self, db_session: AsyncSession):
        """Test comprehensive error handling in user service."""

        # Test invalid email format - this should fail at Pydantic level
        with pytest.raises(ValidationError):
            UserCreate(email="invalid-email", full_name="Test", password="pass")

        # Test completely empty email - this should also fail
        with pytest.raises(ValidationError):
            UserCreate(email="", full_name="Test", password="pass")
