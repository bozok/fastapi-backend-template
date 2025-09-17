# app/core/logging.py

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, ClassVar, Set

from loguru import logger
from pydantic import BaseModel

from app.core.config import settings


class LogConfig(BaseModel):
    """Logging configuration"""

    # Log levels
    LEVEL: str = "INFO"
    FORMAT_DEV: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    FORMAT_PROD: str = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )

    # File logging (for production)
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_FILE_ROTATION: str = "100 MB"
    LOG_FILE_RETENTION: str = "30 days"

    # JSON logging for production
    JSON_LOGS: bool = True
    ENABLE_AUDIT_LOG: bool = True
    ENABLE_PERFORMANCE_LOG: bool = True

    # Sensitive fields to mask - ClassVar since it's not a config field
    SENSITIVE_FIELDS: ClassVar[Set[str]] = {
        "password",
        "token",
        "secret",
        "key",
        "authorization",
        "passwd",
        "pwd",
        "auth",
        "credential",
        "private",
    }


class JsonFormatter:
    """Custom JSON formatter for structured logging"""

    def __init__(self, sensitive_fields: set = None):
        self.sensitive_fields = sensitive_fields or LogConfig.SENSITIVE_FIELDS

    def format(self, record) -> str:
        """Format log record as JSON"""
        # Extract correlation_id from context if available
        correlation_id = getattr(record.get("extra", {}), "correlation_id", None)

        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
            "message": self._mask_sensitive_data(record["message"]),
            "correlation_id": correlation_id,
        }

        # Add extra fields from context
        if "extra" in record:
            extra = record["extra"]
            for key, value in extra.items():
                if key not in log_entry:
                    log_entry[key] = (
                        self._mask_sensitive_data(value)
                        if isinstance(value, str)
                        else value
                    )

        # Add exception info if present
        if record.get("exception"):
            log_entry["exception"] = record["exception"]

        return json.dumps(log_entry, default=str, ensure_ascii=False)

    def _mask_sensitive_data(self, data: Any) -> Any:
        """Mask sensitive data in logs"""
        if isinstance(data, dict):
            return {
                key: "***MASKED***"
                if any(sensitive in key.lower() for sensitive in self.sensitive_fields)
                else self._mask_sensitive_data(value)
                for key, value in data.items()
            }
        elif isinstance(data, str):
            # Simple masking for strings that might contain sensitive data
            for sensitive in self.sensitive_fields:
                if sensitive in data.lower():
                    return "***MASKED***"
            return data
        return data


class LoggingConfig:
    """Centralized logging configuration"""

    def __init__(self):
        self.config = LogConfig()
        self._setup_logging()

    def _setup_logging(self):
        """Setup loguru logging configuration"""
        # Remove default logger
        logger.remove()

        # Development vs Production setup
        if settings.ENVIRONMENT == "development":
            self._setup_development_logging()
        else:
            self._setup_production_logging()

        # Add file logging if needed
        if settings.ENVIRONMENT == "production":
            self._setup_file_logging()

    def _setup_development_logging(self):
        """Setup development-friendly logging"""
        logger.add(
            sys.stdout,
            format=self.config.FORMAT_DEV,
            level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "DEBUG",
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    def _setup_production_logging(self):
        """Setup production JSON logging"""
        formatter = JsonFormatter()

        logger.add(
            sys.stdout,
            format=formatter.format,
            level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO",
            colorize=False,
            backtrace=False,
            diagnose=False,
            serialize=False,  # We handle JSON formatting ourselves
        )

    def _setup_file_logging(self):
        """Setup file logging for production"""
        log_path = Path(self.config.LOG_FILE_PATH)
        log_path.parent.mkdir(exist_ok=True)

        formatter = JsonFormatter()

        logger.add(
            str(log_path),
            format=formatter.format,
            level="INFO",
            rotation=self.config.LOG_FILE_ROTATION,
            retention=self.config.LOG_FILE_RETENTION,
            compression="gz",
            backtrace=True,
            diagnose=True,
        )


# Performance logging decorator
def log_performance(func_name: str = None):
    """Decorator to log function performance"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            import time

            start_time = time.time()
            func_name_to_use = func_name or f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                logger.info(
                    f"Performance: {func_name_to_use} executed successfully",
                    extra={
                        "event_type": "performance",
                        "function_name": func_name_to_use,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "status": "success",
                    },
                )
                return result

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Performance: {func_name_to_use} failed with error",
                    extra={
                        "event_type": "performance",
                        "function_name": func_name_to_use,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "status": "error",
                        "error": str(e),
                    },
                )
                raise

        return wrapper

    return decorator


# Audit logging functions
class AuditLogger:
    """Audit logger for security and compliance events"""

    @staticmethod
    def log_auth_attempt(
        user_email: str, success: bool, ip_address: str = None, user_agent: str = None
    ):
        """Log authentication attempts"""
        logger.info(
            f"Authentication attempt: {user_email}",
            extra={
                "event_type": "audit",
                "event_category": "authentication",
                "user_email": user_email,
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_user_action(
        user_id: str, action: str, resource: str = None, details: Dict = None
    ):
        """Log user actions for audit trail"""
        logger.info(
            f"User action: {action}",
            extra={
                "event_type": "audit",
                "event_category": "user_action",
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_data_access(
        user_id: str, resource_type: str, resource_id: str, operation: str
    ):
        """Log data access for compliance"""
        logger.info(
            f"Data access: {operation} on {resource_type}",
            extra={
                "event_type": "audit",
                "event_category": "data_access",
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "operation": operation,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def log_security_event(
        event_type: str,
        description: str,
        severity: str = "medium",
        details: Dict = None,
    ):
        """Log security events"""
        logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": "audit",
                "event_category": "security",
                "security_event_type": event_type,
                "description": description,
                "severity": severity,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


# Initialize logging
def setup_logging():
    """Initialize the logging system"""
    # logging_config = LoggingConfig()
    logger.info(
        "Logging system initialized",
        extra={"event_type": "system", "component": "logging"},
    )
    return logger


# Get logger instance
def get_logger(name: str = __name__):
    """Get a logger instance with the given name"""
    return logger.bind(logger_name=name)


# Export the audit logger
audit = AuditLogger()
