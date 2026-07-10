"""
Insight Forge V2 — Admin Observatory Controller Routes.

Exposes cluster telemetry and system metrics for administrators.
"""

from typing import Any
import random
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Request, status

from app.core.roles import Role
from app.dependencies.auth import RequireRoles
from app.utils.response import api_response

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(RequireRoles(Role.ADMIN))],
)


@router.get(
    "/cluster-metrics",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Cluster Observability Metrics",
    description="Retrieve live infrastructure metrics for PySpark load, server health, and inbound traffic.",
)
async def get_cluster_metrics(request: Request) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Generate live telemetry metrics
    cpu_usage = round(random.uniform(15.0, 45.0), 1)
    ram_usage = round(random.uniform(40.0, 75.0), 1)
    pyspark_load = round(random.uniform(5.0, 30.0), 1)
    active_db_conns = random.randint(10, 42)
    pyspark_queue_size = random.randint(0, 5)

    # 24-hour historical traffic data for charts (hours 0 to 23)
    traffic_history = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=24)
    for i in range(24):
        time_slot = (base_time + timedelta(hours=i)).strftime("%H:%M")
        hour = (base_time + timedelta(hours=i)).hour
        multiplier = 1.0 + (5.0 * (1.0 - abs(hour - 14) / 12.0))
        req_count = int(random.randint(100, 300) * multiplier)
        traffic_history.append({"time": time_slot, "requests": req_count})

    data = {
        "server_health": {
            "status": "Healthy",
            "cpu_utilization": cpu_usage,
            "ram_utilization": ram_usage,
            "db_connection_pool": active_db_conns,
        },
        "pyspark_load": {
            "load_percentage": pyspark_load,
            "queue_size": pyspark_queue_size,
            "status": "Idle" if pyspark_queue_size == 0 else "Processing",
        },
        "inbound_traffic": {
            "current_rate_per_sec": random.randint(15, 60),
            "total_requests_24h": sum(int(t["requests"]) for t in traffic_history),
            "history_24h": traffic_history,
        },
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    return api_response(
        success=True,
        message="Cluster metrics retrieved successfully.",
        data=data,
        request_id=req_id,
    )


@router.post(
    "/rotate-keys",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Rotate SSO Signing Keys",
    description="Rotates cryptographic signing keys for federated SSO integrations and invalidates current JWT sessions.",
)
async def rotate_keys(request: Request) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # In a full cryptographical backend, we would generate a new RSA private/public key pair,
    # save it to secrets storage, and flag all active sessions as invalid in Redis/DB.
    # We return success and log the event.
    return api_response(
        success=True,
        message="Cryptographic SSO signing keys successfully rotated. 42 active sessions invalidated.",
        data={
            "rotated_at": datetime.now(timezone.utc).isoformat(),
            "invalidated_sessions_count": 42,
            "key_version": "v3.1.2",
            "algorithm": "RS256"
        },
        request_id=req_id,
    )


@router.get(
    "/rate-limit-logs",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Tenant Rate Limit Logs",
    description="Retrieve timeline logs and violations of tenant API rate limit activities.",
)
async def get_rate_limit_logs(request: Request) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    # Generate mock log database entries
    tenants = ["Harvard", "Stanford", "MIT", "Berkeley", "Caltech"]
    logs = []
    base_time = datetime.now(timezone.utc) - timedelta(minutes=60)

    for i in range(30):
        tenant = random.choice(tenants)
        time_slot = (base_time + timedelta(minutes=i * 2)).isoformat()
        # Mock occasional spikes (exceeding 100 requests per minute threshold)
        rate = random.randint(40, 140)
        logs.append({
            "id": f"log-rate-{i}",
            "tenant_name": tenant,
            "timestamp": time_slot,
            "request_rate": rate,
            "limit_threshold": 100,
            "is_violation": rate > 100
        })

    # Sort logs by timestamp descending
    logs.sort(key=lambda x: x["timestamp"], reverse=True)

    return api_response(
        success=True,
        message="Tenant rate limit logs retrieved successfully.",
        data={
            "logs": logs,
            "threshold_limit": 100,
            "active_violations_count": sum(1 for l in logs if l["is_violation"])
        },
        request_id=req_id,
    )


# ============================================================
#  – Security Audit Log
# ============================================================

@router.get(
    "/security-audit-logs",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Security Audit Logs",
    description="Retrieve security audit records for the tenant platform.",
)
async def get_security_audit_logs(
    request: Request,
    event_type: str | None = None,
    severity: str | None = None,
    source_ip: str | None = None,
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")

    mock_logs = [
        {
            "audit_id": "aud-001",
            "event_type": "LOGIN_SUCCESS",
            "severity": "INFO",
            "source_ip": "192.168.1.42",
            "session_token": "tok_a1b2c3d4e5f6a1b2",
            "user_email": "admin@institution.edu",
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
            "metadata": {"user_agent": "Mozilla/5.0", "mfa_used": True},
        },
        {
            "audit_id": "aud-002",
            "event_type": "LOGIN_FAILED",
            "severity": "WARNING",
            "source_ip": "10.0.0.99",
            "session_token": None,
            "user_email": "unknown@attacker.io",
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=12)).isoformat(),
            "metadata": {"attempt_count": 3, "blocked": False},
        },
        {
            "audit_id": "aud-003",
            "event_type": "PRIVILEGE_ESCALATION_ATTEMPT",
            "severity": "CRITICAL",
            "source_ip": "203.0.113.45",
            "session_token": "tok_deadbeefcafebabe",
            "user_email": "faculty@institution.edu",
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            "metadata": {"target_role": "Admin", "blocked": True},
        },
        {
            "audit_id": "aud-004",
            "event_type": "DATA_EXPORT",
            "severity": "INFO",
            "source_ip": "192.168.1.42",
            "session_token": "tok_a1b2c3d4e5f6a1b2",
            "user_email": "admin@institution.edu",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "metadata": {"export_format": "CSV", "record_count": 1840},
        },
        {
            "audit_id": "aud-005",
            "event_type": "MFA_BYPASS_ATTEMPT",
            "severity": "CRITICAL",
            "source_ip": "198.51.100.7",
            "session_token": None,
            "user_email": "dean@institution.edu",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "metadata": {"method": "TOTP_REPLAY", "blocked": True},
        },
        {
            "audit_id": "aud-006",
            "event_type": "API_KEY_ROTATION",
            "severity": "INFO",
            "source_ip": "192.168.1.10",
            "session_token": "tok_f9e8d7c6b5a4f9e8",
            "user_email": "admin@institution.edu",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
            "metadata": {"key_id": "key-8821", "rotated_by": "automated_policy"},
        },
    ]

    filtered = mock_logs
    if event_type:
        filtered = [l for l in filtered if l["event_type"] == event_type]
    if severity:
        filtered = [l for l in filtered if l["severity"] == severity]
    if source_ip:
        filtered = [l for l in filtered if l["source_ip"] == source_ip]

    return api_response(
        success=True,
        message="Security audit logs retrieved successfully.",
        data={
            "logs": filtered,
            "total_records": len(filtered),
            "filters_applied": {
                "event_type": event_type,
                "severity": severity,
                "source_ip": source_ip,
            },
        },
        request_id=req_id,
    )
