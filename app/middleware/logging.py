# app/middleware/logging.py

import time
from typing import Callable, Optional

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.correlation import CorrelationId, set_correlation_id


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging with performance metrics
    """

    def __init__(
        self,
        app,
        exclude_paths: Optional[list] = None,
        mask_query_params: Optional[list] = None,
        mask_headers: Optional[list] = None,
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/favicon.ico"]
        self.mask_query_params = mask_query_params or [
            "password",
            "token",
            "secret",
            "key",
        ]
        self.mask_headers = mask_headers or ["authorization", "cookie", "x-api-key"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with logging"""

        # Skip logging for excluded paths
        if self._should_exclude_path(request.url.path):
            return await call_next(request)

        # Generate or extract correlation ID
        correlation_id = self._get_or_set_correlation_id(request)

        # Bind correlation ID to logger context
        request_logger = logger.bind(correlation_id=correlation_id)

        # Start timing
        start_time = time.time()

        # Log incoming request
        await self._log_request(request, request_logger, correlation_id)

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log successful response
            await self._log_response(
                request, response, request_logger, correlation_id, process_time
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"

            return response

        except Exception as e:
            # Calculate processing time for errors
            process_time = time.time() - start_time

            # Log error
            await self._log_error(
                request, e, request_logger, correlation_id, process_time
            )

            # Re-raise the exception
            raise

    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from logging"""
        return any(excluded in path for excluded in self.exclude_paths)

    def _get_or_set_correlation_id(self, request: Request) -> str:
        """Get correlation ID from headers or generate new one"""
        # Try to get correlation ID from headers
        correlation_id = request.headers.get("X-Correlation-ID")

        if not correlation_id:
            correlation_id = CorrelationId.generate()

        # Set correlation ID in context
        set_correlation_id(correlation_id)

        return correlation_id

    async def _log_request(self, request: Request, request_logger, correlation_id: str):
        """Log incoming request details"""

        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "Unknown")

        # Parse and mask query parameters
        query_params = self._mask_query_params(dict(request.query_params))

        # Mask sensitive headers
        headers = self._mask_headers(dict(request.headers))

        # Get request body size
        body_size = request.headers.get("Content-Length", "0")

        request_logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "event_type": "request",
                "request_method": request.method,
                "request_path": request.url.path,
                "request_query_params": query_params,
                "request_headers": headers,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "body_size": body_size,
                "correlation_id": correlation_id,
            },
        )

    async def _log_response(
        self,
        request: Request,
        response: Response,
        request_logger,
        correlation_id: str,
        process_time: float,
    ):
        """Log response details with performance metrics"""

        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"

        # Get response size
        response_size = response.headers.get("Content-Length", "0")

        # Performance classification
        perf_category = self._classify_performance(process_time)

        getattr(request_logger, log_level)(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "event_type": "response",
                "request_method": request.method,
                "request_path": request.url.path,
                "response_status_code": response.status_code,
                "response_size": response_size,
                "process_time_ms": round(process_time * 1000, 2),
                "process_time_seconds": round(process_time, 4),
                "performance_category": perf_category,
                "correlation_id": correlation_id,
            },
        )

        # Log performance warning if slow
        if process_time > 1.0:  # More than 1 second
            request_logger.warning(
                f"Slow request detected: {request.method} {request.url.path}",
                extra={
                    "event_type": "performance",
                    "event_category": "slow_request",
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "process_time_ms": round(process_time * 1000, 2),
                    "correlation_id": correlation_id,
                },
            )

    async def _log_error(
        self,
        request: Request,
        error: Exception,
        request_logger,
        correlation_id: str,
        process_time: float,
    ):
        """Log request errors"""

        request_logger.error(
            f"Request failed: {request.method} {request.url.path} - {type(error).__name__}: {str(error)}",
            extra={
                "event_type": "error",
                "request_method": request.method,
                "request_path": request.url.path,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "process_time_ms": round(process_time * 1000, 2),
                "correlation_id": correlation_id,
            },
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers (load balancer, proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return getattr(request.client, "host", "unknown")

    def _mask_query_params(self, params: dict) -> dict:
        """Mask sensitive query parameters"""
        masked_params = {}
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in self.mask_query_params):
                masked_params[key] = "***MASKED***"
            else:
                masked_params[key] = value
        return masked_params

    def _mask_headers(self, headers: dict) -> dict:
        """Mask sensitive headers"""
        masked_headers = {}
        for key, value in headers.items():
            if any(sensitive in key.lower() for sensitive in self.mask_headers):
                masked_headers[key] = "***MASKED***"
            else:
                masked_headers[key] = value
        return masked_headers

    def _classify_performance(self, process_time: float) -> str:
        """Classify request performance"""
        if process_time < 0.1:
            return "fast"
        elif process_time < 0.5:
            return "normal"
        elif process_time < 1.0:
            return "slow"
        else:
            return "very_slow"


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Specialized middleware for detailed performance monitoring
    """

    def __init__(self, app, slow_threshold: float = 1.0):
        super().__init__(app)
        self.slow_threshold = slow_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance with detailed metrics"""

        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            response = await call_next(request)

            end_time = time.time()
            end_memory = self._get_memory_usage()

            process_time = end_time - start_time
            memory_delta = end_memory - start_memory

            # Log performance metrics
            self._log_performance_metrics(request, response, process_time, memory_delta)

            return response

        except Exception as e:
            end_time = time.time()
            process_time = end_time - start_time

            logger.error(
                "Performance monitoring - Request failed",
                extra={
                    "event_type": "performance",
                    "event_category": "request_error",
                    "path": request.url.path,
                    "method": request.method,
                    "process_time_ms": round(process_time * 1000, 2),
                    "error": str(e),
                },
            )
            raise

    def _log_performance_metrics(
        self,
        request: Request,
        response: Response,
        process_time: float,
        memory_delta: float,
    ):
        """Log detailed performance metrics"""

        metrics = {
            "event_type": "performance",
            "event_category": "request_metrics",
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "memory_delta_mb": round(memory_delta, 2),
            "is_slow": process_time > self.slow_threshold,
        }

        if process_time > self.slow_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path}",
                extra=metrics,
            )
        else:
            logger.info(
                f"Request performance: {request.method} {request.url.path}",
                extra=metrics,
            )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0  # psutil not available
