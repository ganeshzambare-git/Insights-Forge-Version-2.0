from datetime import datetime, timezone
from typing import Any


def api_response(
    success: bool,
    message: str = "",
    data: Any = None,
    meta: Any = None,
    errors: list[dict[str, Any]] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Structure a standardized JSON envelope matching enterprise specifications.

    Args:
        success: True for 2xx responses, False otherwise.
        message: Descriptive outcomes text.
        data: Payload payload data.
        meta: Pagination/metadata payload.
        errors: List of structured errors.
        request_id: Correlation tracing ID.

    Returns:
        A dictionary envelope ready for JSON serialization.
    """
    meta_dict = {
        "request_id": request_id or "unknown-req-id",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_version": "2.0.0",
    }
    if meta and isinstance(meta, dict):
        meta_dict.update(meta)

    return {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
        "meta": meta_dict,
        "errors": errors if errors is not None else [],
    }
