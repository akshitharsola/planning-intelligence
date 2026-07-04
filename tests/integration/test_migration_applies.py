from sqlalchemy import inspect

from src.core.db.session import engine


def test_applications_table_exists():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "applications" in tables
    assert "application_events" in tables


def test_applications_has_natural_key_unique_constraint():
    inspector = inspect(engine)
    constraints = inspector.get_unique_constraints("applications")
    assert any(
        set(c["column_names"]) == {"planning_authority", "application_ref"}
        for c in constraints
    )


def test_applications_has_search_indexes():
    inspector = inspect(engine)
    indexes = inspector.get_indexes("applications")
    index_columns = {tuple(idx["column_names"]) for idx in indexes}

    assert ("planning_status_current",) in index_columns
    assert ("application_type",) in index_columns
    assert ("date_received",) in index_columns


def test_applications_has_trigram_indexes_for_ilike_search():
    # Queries pg_am/pg_opclass system catalogs directly (access method +
    # operator class) instead of pattern-matching the human-readable
    # indexdef string, so this doesn't depend on how a given Postgres
    # version happens to format index DDL text.
    from sqlalchemy import text
    from src.core.db.session import SessionLocal

    session = SessionLocal()
    try:
        result = session.execute(
            text(
                """
                SELECT DISTINCT a.attname AS column_name
                FROM pg_index ix
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_class t ON t.oid = ix.indrelid
                JOIN pg_am am ON am.oid = i.relam
                JOIN pg_attribute a
                    ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                JOIN pg_opclass opc ON opc.oid = ix.indclass[0]
                WHERE t.relname = 'applications'
                  AND am.amname = 'gin'
                  AND opc.opcname = 'gin_trgm_ops'
                """
            )
        ).fetchall()
    finally:
        session.close()

    trigram_columns = {row[0] for row in result}
    assert "applicant_name" in trigram_columns
    assert "site_address" in trigram_columns
    assert "development_description" in trigram_columns
