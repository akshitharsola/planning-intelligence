"""
Minimal ingestion KPIs: rows ingested per run, per-region parser error
counts/rates. No dashboard/alerting in this foundation pass — just
structured counters that a later insight_service or external dashboard
can read. Per spec section 3.
"""

from collections import defaultdict

_counters: dict[str, dict[str, int]] = defaultdict(
    lambda: {"rows_ingested_total": 0, "parse_errors_total": 0, "runs_total": 0}
)


def record_ingestion_run(region: str, rows_ingested: int, parse_errors: int) -> None:
    bucket = _counters[region]
    bucket["rows_ingested_total"] += rows_ingested
    bucket["parse_errors_total"] += parse_errors
    bucket["runs_total"] += 1


def get_metrics_snapshot(region: str) -> dict[str, int]:
    return dict(_counters[region])
