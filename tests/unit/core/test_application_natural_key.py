from sqlalchemy import UniqueConstraint

from src.core.models.application import Application


def test_application_has_natural_key_constraint():
    constraints = [
        c for c in Application.__table__.constraints
        if isinstance(c, UniqueConstraint)
    ]
    assert any(
        set(c.columns.keys()) == {"planning_authority", "application_ref"}
        for c in constraints
    )
