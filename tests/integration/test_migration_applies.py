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
