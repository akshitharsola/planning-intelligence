from src.monitoring.metrics import get_metrics_snapshot, record_ingestion_run


def test_record_ingestion_run_increments_counters():
    record_ingestion_run(region="galway_city", rows_ingested=10, parse_errors=1)
    record_ingestion_run(region="galway_city", rows_ingested=5, parse_errors=0)
    snapshot = get_metrics_snapshot("galway_city")
    assert snapshot["rows_ingested_total"] == 15
    assert snapshot["parse_errors_total"] == 1
    assert snapshot["runs_total"] == 2
