"""
Insight Forge V2 — Base Service.

Declares the BaseService housing UnitofWork management and operation lifecycles.
"""

import time
from typing import Any, Awaitable, Callable, TypeVar
from app.services.uow import UnitOfWork
from app.services.context import ServiceContext
from app.services.audit import AuditLoggerProtocol
from app.services.providers import ClockProvider, UUIDProvider
from app.services.result import ServiceResult
from app.services.exceptions import ServiceError

T = TypeVar("T")


class BaseService:
    """Core Service boundary exposing standardized command lifecycles and transactions."""

    def __init__(
        self,
        uow: UnitOfWork,
        context: ServiceContext,
        audit_logger: AuditLoggerProtocol,
        clock: ClockProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        """Initialize the base service.

        Args:
            uow: Injected UnitOfWork instance.
            context: Active ServiceContext metadata.
            audit_logger: Swappable audit logger protocol.
            clock: Time-aware Clock provider.
            uuid_provider: Unique identifier generator provider.
        """
        self.uow = uow
        self.context = context
        self.audit_logger = audit_logger
        self.clock = clock
        self.uuid_provider = uuid_provider

    def publish_domain_event(self, event_name: str, payload: dict[str, Any]) -> None:
        """Extension hook placeholder for future event-driven message dispatching."""
        pass

    async def execute_command(
        self,
        operation: str,
        action: Callable[[], Awaitable[T]],
        success_msg: str | None = None,
    ) -> ServiceResult[T]:
        """Execute a state-mutating command within an atomic UnitOfWork transaction.

        Args:
            operation: Name of the executed service method.
            action: Async callable performing repository operations.
            success_msg: User-facing success descriptive message.

        Returns:
            A ServiceResult wrapping the transaction result.
        """
        service_name = self.__class__.__name__
        self.audit_logger.started(service_name, operation, self.context)
        start_time = time.perf_counter()

        try:
            async with self.uow:
                result_data = await action()
                # Flush session memory within the context block
                await self.uow.flush()

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            self.audit_logger.succeeded(
                service_name,
                operation,
                self.context,
                duration_ms,
                f"Completed: {success_msg}" if success_msg else None,
            )
            return ServiceResult(success=True, data=result_data, message=success_msg)

        except ServiceError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            self.audit_logger.failed(
                service_name, operation, self.context, duration_ms, e
            )
            raise
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            wrapped_error = ServiceError(
                f"Unexpected operational failure: {str(e)}",
                error_code="unexpected_error",
            )
            self.audit_logger.failed(
                service_name, operation, self.context, duration_ms, wrapped_error
            )
            raise wrapped_error from e
