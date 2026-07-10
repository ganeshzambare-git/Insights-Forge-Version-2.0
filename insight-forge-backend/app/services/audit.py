"""
Insight Forge V2 — Service Audit Logger.

Provides structured auditing for operation lifecycle events (start, success, fail).
"""

import logging
from typing import Protocol
from app.services.context import ServiceContext

logger = logging.getLogger("app.services.audit")


class AuditLoggerProtocol(Protocol):
    """Protocol defining audit logging operations for service methods."""

    def started(self, service: str, operation: str, context: ServiceContext) -> None:
        """Record the initiation of an operation.

        Args:
            service: Class name of the service.
            operation: Name of the executed method.
            context: Active ServiceContext instance.
        """
        ...

    def succeeded(
        self,
        service: str,
        operation: str,
        context: ServiceContext,
        duration_ms: float,
        detail: str | None = None,
    ) -> None:
        """Record the successful completion of an operation.

        Args:
            service: Class name of the service.
            operation: Name of the executed method.
            context: Active ServiceContext instance.
            duration_ms: Request processing duration in milliseconds.
            detail: Optional extra details payload.
        """
        ...

    def failed(
        self,
        service: str,
        operation: str,
        context: ServiceContext,
        duration_ms: float,
        error: Exception,
    ) -> None:
        """Record the failed execution of an operation.

        Args:
            service: Class name of the service.
            operation: Name of the executed method.
            context: Active ServiceContext instance.
            duration_ms: Process duration up to failure in milliseconds.
            error: The raised exception instance.
        """
        ...

    def security_event(
        self,
        event: str,
        context: ServiceContext,
        duration_ms: float = 0.0,
        detail: str | None = None,
    ) -> None:
        """Record specific security boundary events (e.g. LOGIN_SUCCESS, ACCESS_DENIED).

        Args:
            event: The uppercase audit event name.
            context: Active ServiceContext instance.
            duration_ms: Optional execution time in milliseconds.
            detail: Optional descriptive text.
        """
        ...


class DefaultAuditLogger:
    """Standard system audit logger pushing structured events to JSON logging formatter."""

    def started(self, service: str, operation: str, context: ServiceContext) -> None:
        """Log started operation event."""
        extra = {
            "service": service,
            "operation": operation,
            "tenant_id": str(context.tenant_id) if context.tenant_id else None,
            "user_id": str(context.user_id) if context.user_id else None,
            "request_id": context.request_id,
            "status": "started",
            "duration_ms": 0.0,
        }
        logger.info(f"Operation started: {service}.{operation}", extra=extra)

    def succeeded(
        self,
        service: str,
        operation: str,
        context: ServiceContext,
        duration_ms: float,
        detail: str | None = None,
    ) -> None:
        """Log succeeded operation event."""
        extra = {
            "service": service,
            "operation": operation,
            "tenant_id": str(context.tenant_id) if context.tenant_id else None,
            "user_id": str(context.user_id) if context.user_id else None,
            "request_id": context.request_id,
            "status": "succeeded",
            "duration_ms": duration_ms,
        }
        msg = f"Operation succeeded: {service}.{operation}"
        if detail:
            msg += f" - {detail}"
        logger.info(msg, extra=extra)

    def failed(
        self,
        service: str,
        operation: str,
        context: ServiceContext,
        duration_ms: float,
        error: Exception,
    ) -> None:
        """Log failed operation event."""
        extra = {
            "service": service,
            "operation": operation,
            "tenant_id": str(context.tenant_id) if context.tenant_id else None,
            "user_id": str(context.user_id) if context.user_id else None,
            "request_id": context.request_id,
            "status": "failed",
            "duration_ms": duration_ms,
        }
        logger.error(
            f"Operation failed: {service}.{operation} - Error: {str(error)}",
            extra=extra,
        )

    def security_event(
        self,
        event: str,
        context: ServiceContext,
        duration_ms: float = 0.0,
        detail: str | None = None,
    ) -> None:
        """Record specific security boundary events."""
        extra = {
            "service": "Security",
            "operation": event,
            "tenant_id": str(context.tenant_id) if context.tenant_id else None,
            "user_id": str(context.user_id) if context.user_id else None,
            "request_id": context.request_id,
            "status": event,
            "duration_ms": duration_ms,
        }
        msg = f"Security Event [{event}]"
        if detail:
            msg += f" - {detail}"
        if "FAILED" in event or "DENIED" in event or "REUSE" in event:
            logger.error(msg, extra=extra)
        else:
            logger.info(msg, extra=extra)
