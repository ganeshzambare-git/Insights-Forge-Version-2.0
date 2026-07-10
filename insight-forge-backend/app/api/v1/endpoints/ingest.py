"""
Insight Forge V2 — V1 Dataset Ingestion and Chunk Upload Controller.

Exposes endpoints for chunked file streaming and structural checks.
"""

from typing import Any
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, status

from app.core.roles import Role
from app.dependencies.auth import RequireRoles
from app.utils.response import api_response

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
    dependencies=[Depends(RequireRoles(Role.ADMIN))],
)


@router.post(
    "/upload-telemetry",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Upload Dataset Chunk Telemetry",
    description="Stream chunked data partitions (1 MB chunks) for high-scale document analytics.",
)
async def upload_telemetry(
    request: Request,
    file_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Read uploaded block
    contents = await file.read()
    bytes_received = len(contents)

    # Process chunk (mock save chunk)
    return api_response(
        success=True,
        message=f"Chunk {chunk_index + 1}/{total_chunks} processed successfully.",
        data={
            "file_id": file_id,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "bytes_received": bytes_received,
            "status": "Processing" if chunk_index + 1 < total_chunks else "Completed"
        },
        request_id=req_id,
    )


@router.get(
    "/dead-letter-logs",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Ingestion Dead-Letter Logs",
    description="Retrieve malformed payload records flagged for schema corrections.",
)
async def get_dead_letter_logs(request: Request) -> dict[str, Any]:
    from datetime import datetime, timezone
    req_id = getattr(request.state, "request_id", "unknown-req-id")
    logs = [
        {
            "payload_id": "err-90921",
            "error_summary": "Missing required field: tenant_id",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "Failed"
        },
        {
            "payload_id": "err-90922",
            "error_summary": "Schema type mismatch: gpa expected float, got string 'A+'",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "Failed"
        }
    ]
    return api_response(
        success=True,
        message="Ingestion dead-letter logs retrieved successfully.",
        data={"logs": logs},
        request_id=req_id,
    )

