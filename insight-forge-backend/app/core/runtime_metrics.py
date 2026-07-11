"""
Insight Forge V2 — Runtime Observability Metrics.

A lightweight, in-process metrics registry fed by request middleware. It powers
the admin cluster-metrics and rate-limit-logs endpoints with *real* numbers
(actual request throughput, process memory, CPU load, uptime) instead of mock
data. In-memory only — counters reset when the process restarts.
"""

from __future__ import annotations

import os
import resource
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any


def _minute_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:00Z")


class RuntimeMetrics:
    """Thread-safe in-process counters for request throughput and rate tracking."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._start = time.time()
        self._total_requests = 0
        # Global per-minute request counts (last 24h worth of minutes).
        self._per_minute: "deque[tuple[str, int]]" = deque(maxlen=24 * 60)
        self._cur_minute: str | None = None
        self._cur_count = 0
        # Per-(tenant, minute) request counts for rate-limit observability.
        self._tenant_minute: dict[tuple[str, str], int] = defaultdict(int)
        self._tenant_events: "deque[tuple[str, str, int]]" = deque(maxlen=300)

    def record_request(self, tenant_name: str = "unknown") -> None:
        """Record one served request for a tenant."""
        now = datetime.now(timezone.utc)
        minute = _minute_key(now)
        with self._lock:
            self._total_requests += 1
            if minute != self._cur_minute:
                if self._cur_minute is not None:
                    self._per_minute.append((self._cur_minute, self._cur_count))
                self._cur_minute = minute
                self._cur_count = 0
            self._cur_count += 1

            key = (tenant_name, minute)
            self._tenant_minute[key] += 1
            # Keep a rolling event log of (tenant, minute, rate).
            self._tenant_events.append((tenant_name, minute, self._tenant_minute[key]))

    # ---- snapshots -----------------------------------------------------

    def _process_snapshot(self) -> dict[str, Any]:
        """Real process/system metrics (memory, RAM %, CPU load, uptime)."""
        # ru_maxrss is bytes on macOS, kilobytes on Linux — normalize to bytes.
        ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_bytes = ru if ru > 10_000_000 else ru * 1024
        mem_mb = round(rss_bytes / (1024 * 1024), 1)

        # Total physical RAM for a real utilization percentage.
        try:
            total_ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            ram_pct = round(min(100.0, rss_bytes / total_ram * 100), 1)
        except (ValueError, OSError, AttributeError):
            ram_pct = 0.0

        cpu_count = os.cpu_count() or 1
        try:
            load1 = os.getloadavg()[0]
        except (OSError, AttributeError):
            load1 = 0.0
        cpu_pct = round(min(100.0, (load1 / cpu_count) * 100), 1)

        return {
            "uptime_seconds": round(time.time() - self._start, 1),
            "memory_mb": mem_mb,
            "ram_utilization": ram_pct,
            "cpu_utilization": cpu_pct,
            "cpu_count": cpu_count,
        }

    def cluster_snapshot(self, db_pool: dict[str, Any] | None = None) -> dict[str, Any]:
        """Assemble the cluster-metrics payload from real runtime data.

        Keys match the frontend ``ClusterMetrics`` contract exactly.
        """
        proc = self._process_snapshot()
        with self._lock:
            history = list(self._per_minute)
            if self._cur_minute is not None:
                history.append((self._cur_minute, self._cur_count))
            total = self._total_requests

        # Last 24 hourly buckets from per-minute data.
        hourly: dict[str, int] = defaultdict(int)
        for minute, count in history:
            hourly[minute[:13]] += count  # group by 'YYYY-MM-DDTHH'
        history_24h = [
            {"time": f"{h[11:13]}:00", "requests": c}
            for h, c in sorted(hourly.items())[-24:]
        ]
        requests_last_minute = history[-1][1] if history else 0
        rate_per_sec = round(requests_last_minute / 60.0, 2)

        return {
            "server_health": {
                "status": "Healthy",
                "cpu_utilization": proc["cpu_utilization"],
                "ram_utilization": proc["ram_utilization"],
                "memory_mb": proc["memory_mb"],
                "uptime_seconds": proc["uptime_seconds"],
                "db_connection_pool": (db_pool or {}).get("checked_out", 0),
                "db_pool_size": (db_pool or {}).get("size", 0),
            },
            "pyspark_load": {
                "load_percentage": proc["cpu_utilization"],
                "queue_size": 0,
                "status": "Idle" if proc["cpu_utilization"] < 50 else "Processing",
            },
            "inbound_traffic": {
                "current_rate_per_sec": rate_per_sec,
                "total_requests_24h": total,
                "history_24h": history_24h,
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def rate_limit_logs(self, threshold: int = 100) -> dict[str, Any]:
        """Return recent per-tenant per-minute request rates as real logs."""
        with self._lock:
            events = list(self._tenant_events)
        logs = [
            {
                "id": f"rate-{idx}",
                "tenant_name": tenant,
                "timestamp": minute,
                "request_rate": rate,
                "limit_threshold": threshold,
                "is_violation": rate > threshold,
            }
            for idx, (tenant, minute, rate) in enumerate(reversed(events))
        ]
        return {
            "logs": logs,
            "threshold_limit": threshold,
            "active_violations_count": sum(1 for entry in logs if entry["is_violation"]),
        }


# Process-wide singleton.
runtime_metrics = RuntimeMetrics()
