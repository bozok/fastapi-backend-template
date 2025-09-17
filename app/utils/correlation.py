# app/utils/correlation.py

import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable to store correlation ID across async calls
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


class CorrelationId:
    """Correlation ID management for request tracking"""

    @staticmethod
    def generate() -> str:
        """Generate a new correlation ID"""
        return str(uuid.uuid4())

    @staticmethod
    def set(correlation_id: str) -> None:
        """Set the correlation ID for the current context"""
        correlation_id_var.set(correlation_id)

    @staticmethod
    def get() -> Optional[str]:
        """Get the current correlation ID"""
        return correlation_id_var.get()

    @staticmethod
    def get_or_generate() -> str:
        """Get current correlation ID or generate a new one"""
        current_id = correlation_id_var.get()
        if current_id is None:
            current_id = CorrelationId.generate()
            CorrelationId.set(current_id)
        return current_id


def get_correlation_id() -> Optional[str]:
    """Convenience function to get correlation ID"""
    return CorrelationId.get()


def set_correlation_id(correlation_id: str) -> None:
    """Convenience function to set correlation ID"""
    CorrelationId.set(correlation_id)
