"""
Logging and audit trail tests.

Tests for logging functionality, audit trails, and security event logging.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import get_logger, audit
from app.models.user import User


@pytest.mark.unit
class TestBasicLogging:
    """Test basic logging functionality."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a valid logger."""
        logger = get_logger(__name__)

        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")

    def test_logger_with_extra_fields(self):
        """Test logger with extra structured fields."""
        logger = get_logger(__name__)

        with patch.object(logger, "info") as mock_info:
            logger.info(
                "Test message",
                extra={"event_type": "test", "user_id": "123", "action": "test_action"},
            )

            # Verify info was called with message and extra fields
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert call_args[0][0] == "Test message"
            assert "extra" in call_args[1]
            assert call_args[1]["extra"]["event_type"] == "test"

    def test_logger_different_levels(self):
        """Test different logging levels."""
        logger = get_logger(__name__)

        with (
            patch.object(logger, "debug") as mock_debug,
            patch.object(logger, "info") as mock_info,
            patch.object(logger, "warning") as mock_warning,
            patch.object(logger, "error") as mock_error,
        ):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            mock_debug.assert_called_once_with("Debug message")
            mock_info.assert_called_once_with("Info message")
            mock_warning.assert_called_once_with("Warning message")
            mock_error.assert_called_once_with("Error message")


@pytest.mark.unit
class TestAuditLogging:
    """Test audit logging functionality."""

    def test_log_auth_attempt_success(self):
        """Test logging successful authentication attempt."""
        with patch("app.core.logging.logger") as mock_logger:
            audit.log_auth_attempt(
                user_email="test@example.com",
                success=True,
                ip_address="192.168.1.1",
                user_agent="test-agent",
            )

            # Verify logger was called
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args

            # Check log message
            assert "Authentication attempt: test@example.com" in call_args[0][0]

            # Check extra fields
            extra = call_args[1]["extra"]
            assert extra["event_type"] == "audit"
            assert extra["event_category"] == "authentication"
            assert extra["user_email"] == "test@example.com"
            assert extra["ip_address"] == "192.168.1.1"
            assert extra["user_agent"] == "test-agent"

    def test_log_auth_attempt_failure(self):
        """Test logging failed authentication attempt."""
        with patch("app.core.logging.logger") as mock_logger:
            audit.log_auth_attempt(
                user_email="test@example.com",
                success=False,
                ip_address="192.168.1.1",
                user_agent="test-agent",
            )

            # Verify logger was called (auth attempts use info level)
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args

            # Check log message
            assert "Authentication attempt" in call_args[0][0]

            # Check extra fields
            extra = call_args[1]["extra"]
            assert extra["event_type"] == "audit"
            assert extra["event_category"] == "authentication"
            assert extra["user_email"] == "test@example.com"

    def test_log_user_action(self):
        """Test logging user actions."""
        with patch("app.core.logging.logger") as mock_logger:
            audit.log_user_action(
                user_id="123",
                action="user_created",
                resource="user:456",
                details={"email": "test@example.com"},
            )

            # Verify logger was called
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args

            # Check log message
            assert "User action: user_created" in call_args[0][0]

            # Check extra fields
            extra = call_args[1]["extra"]
            assert extra["event_type"] == "audit"
            assert extra["event_category"] == "user_action"
            assert extra["user_id"] == "123"
            assert extra["action"] == "user_created"
            assert extra["resource"] == "user:456"
            assert extra["details"] == {"email": "test@example.com"}

    def test_log_security_event(self):
        """Test logging security events."""
        with patch("app.core.logging.logger") as mock_logger:
            audit.log_security_event(
                event_type="suspicious_activity",
                description="Multiple failed login attempts",
                severity="high",
                details={"attempts": 5, "timeframe": "5 minutes"},
            )

            # Verify logger was called (security events use warning level)
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args

            # Check log message
            assert "Security event: suspicious_activity" in call_args[0][0]

            # Check extra fields
            extra = call_args[1]["extra"]
            assert extra["event_type"] == "audit"
            assert extra["event_category"] == "security"
            assert extra["security_event_type"] == "suspicious_activity"
            assert extra["severity"] == "high"
            assert extra["details"] == {"attempts": 5, "timeframe": "5 minutes"}

    def test_log_security_event_different_severities(self):
        """Test security event logging with different severity levels."""
        with patch("app.core.logging.logger") as mock_logger:
            # Test different severities - all use warning level
            severities = ["low", "medium", "high", "critical"]

            for severity in severities:
                audit.log_security_event(
                    event_type="test_event",
                    description="Test description",
                    severity=severity,
                )

                # All security events use warning level
                mock_logger.warning.assert_called()

                # Check that the severity is stored in extra data
                call_args = mock_logger.warning.call_args
                extra = call_args[1]["extra"]
                assert extra["severity"] == severity

                # Reset for next iteration
                mock_logger.reset_mock()

    def test_log_data_access(self):
        """Test logging data access events."""
        with patch("app.core.logging.logger") as mock_logger:
            audit.log_data_access(
                user_id="123",
                resource_type="user_profile",
                resource_id="456",
                operation="read",
            )

            # Verify logger was called
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args

            # Check log message
            assert "Data access: read on user_profile" in call_args[0][0]

            # Check extra fields
            extra = call_args[1]["extra"]
            assert extra["event_type"] == "audit"
            assert extra["event_category"] == "data_access"
            assert extra["user_id"] == "123"
            assert extra["resource_type"] == "user_profile"
            assert extra["resource_id"] == "456"
            assert extra["operation"] == "read"


@pytest.mark.integration
@pytest.mark.asyncio
class TestLoggingIntegration:
    """Test logging integration with actual application flows."""

    async def test_user_creation_logging_flow(self, db_session: AsyncSession):
        """Test complete logging flow during user creation."""
        from app.services.user import user_service
        from app.schemas.user import UserCreate

        with (
            patch("app.services.user.logger") as mock_service_logger,
            patch("app.core.logging.audit.log_user_action") as mock_log_action,
            patch("app.core.logging.audit.log_security_event") as mock_log_security,
        ):
            user_data = UserCreate(
                email="logging_test@example.com",
                full_name="Logging Test User",
                password="password123",
            )

            created_user = await user_service.create_user(db_session, user_in=user_data)

            # Verify service logging was called
            mock_service_logger.info.assert_called()

            # Verify audit logging was called
            mock_log_action.assert_called()
            mock_log_security.assert_called()

            # Check audit log details
            action_call = mock_log_action.call_args
            assert action_call[1]["user_id"] == str(created_user.id)
            assert action_call[1]["action"] == "user_registration"

            # Check security event details
            security_call = mock_log_security.call_args
            assert security_call[0][0] == "user_registration"
            assert security_call[1]["severity"] == "info"

    async def test_authentication_logging_flow(self, client, test_user: User):
        """Test logging flow during authentication."""

        with (
            patch("app.core.logging.get_logger") as mock_get_logger,
            patch("app.core.logging.audit.log_auth_attempt") as mock_log_auth,
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Perform login
            response = await client.post(
                "/api/v1/auth/login",
                data={"username": test_user.email, "password": "testpassword123"},
            )

            assert response.status_code == 200

            # Verify authentication logging was called
            mock_log_auth.assert_called()

            # Check successful auth log
            auth_call = mock_log_auth.call_args
            assert auth_call[1]["user_email"] == test_user.email
            assert auth_call[1]["success"] is True

    async def test_failed_authentication_logging(self, client, test_user: User):
        """Test logging flow during failed authentication."""
        with (
            patch("app.core.logging.get_logger") as mock_get_logger,
            patch("app.core.logging.audit.log_auth_attempt") as mock_log_auth,
        ):
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Perform failed login
            response = await client.post(
                "/api/v1/auth/login",
                data={"username": test_user.email, "password": "wrongpassword"},
            )

            assert response.status_code == 401

            # Verify failed authentication logging was called
            mock_log_auth.assert_called()

            # Check failed auth log
            auth_call = mock_log_auth.call_args
            assert auth_call[1]["user_email"] == test_user.email
            assert auth_call[1]["success"] is False


@pytest.mark.unit
class TestPerformanceLogging:
    """Test performance logging functionality."""

    def test_log_performance_decorator(self):
        """Test the log_performance decorator."""
        from app.core.logging import log_performance

        with patch("app.core.logging.logger") as mock_logger:

            @log_performance("test_operation")
            async def test_function():
                """Test function for performance logging."""
                await asyncio.sleep(0.01)  # Small delay
                return "test_result"

            import asyncio

            # Run the decorated function
            result = asyncio.run(test_function())

            assert result == "test_result"

            # Verify performance logging was called
            mock_logger.info.assert_called()

            # Check that performance metrics were logged
            calls = mock_logger.info.call_args_list
            performance_call = None
            for call in calls:
                if "Performance:" in call[0][0]:
                    performance_call = call
                    break

            assert performance_call is not None
            extra = performance_call[1]["extra"]
            assert extra["event_type"] == "performance"
            assert extra["function_name"] == "test_operation"
            assert "execution_time_ms" in extra
            assert extra["execution_time_ms"] >= 0  # Allow for very fast execution


@pytest.mark.unit
class TestLogFormatting:
    """Test log formatting and structure."""

    def test_structured_log_format(self):
        """Test that logs are properly structured."""
        with patch("app.core.logging.logger") as mock_logger:
            # Test structured logging with various field types
            audit.log_user_action(
                user_id="123",
                action="test_action",
                details={
                    "string_field": "test_value",
                    "number_field": 42,
                    "boolean_field": True,
                    "list_field": ["item1", "item2"],
                    "nested_object": {"key": "value"},
                },
            )

            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args

            # Verify extra fields are properly structured
            extra = call_args[1]["extra"]
            assert extra["event_type"] == "audit"
            assert extra["event_category"] == "user_action"
            assert extra["user_id"] == "123"
            assert extra["action"] == "test_action"

            # Verify complex details are preserved
            details = extra["details"]
            assert details["string_field"] == "test_value"
            assert details["number_field"] == 42
            assert details["boolean_field"] is True
            assert details["list_field"] == ["item1", "item2"]
            assert details["nested_object"]["key"] == "value"

    def test_log_message_consistency(self):
        """Test that log messages follow consistent format."""
        with patch("app.core.logging.logger") as mock_logger:
            # Test different audit log types
            audit.log_auth_attempt("test@example.com", True, "127.0.0.1", "test-agent")
            audit.log_user_action("123", "test_action")
            audit.log_security_event("test_event", "Test description", "medium")
            audit.log_data_access("123", "user_profile", "456", "read")

            # Verify all calls were made
            assert (
                mock_logger.info.call_count == 3
            )  # auth success, user action, data access
            assert mock_logger.warning.call_count == 1  # security event medium severity

            # Check message formats
            all_calls = (
                mock_logger.info.call_args_list + mock_logger.warning.call_args_list
            )

            for call in all_calls:
                message = call[0][0]
                extra = call[1]["extra"]

                # All messages should have consistent structure
                assert isinstance(message, str)
                assert len(message) > 0
                assert "event_type" in extra
                assert isinstance(extra["event_type"], str)


@pytest.mark.integration
class TestLoggingConfiguration:
    """Test logging configuration and setup."""

    def test_logger_configuration(self):
        """Test that loggers are properly configured."""
        logger = get_logger("test.module")

        # Verify logger has expected loguru attributes and methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")
        assert callable(logger.info)

    def test_audit_logger_availability(self):
        """Test that audit logging functions are available."""
        # Verify all audit functions exist and are callable
        assert callable(audit.log_auth_attempt)
        assert callable(audit.log_user_action)
        assert callable(audit.log_security_event)
        assert callable(audit.log_data_access)

    def test_log_correlation_ids(self):
        """Test log correlation ID functionality if implemented."""
        from app.utils.correlation import (
            get_correlation_id,
            set_correlation_id,
            CorrelationId,
        )

        # Test correlation ID generation
        test_id = CorrelationId.generate()
        assert test_id is not None
        assert isinstance(test_id, str)
        assert len(test_id) > 0

        # Test setting and getting correlation ID
        set_correlation_id(test_id)
        retrieved_id = get_correlation_id()
        assert retrieved_id == test_id

        # Test get_or_generate
        auto_id = CorrelationId.get_or_generate()
        assert auto_id == test_id  # Should return existing ID
