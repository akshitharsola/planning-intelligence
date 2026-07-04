from datetime import date
from unittest.mock import patch

from src.core.db.session import SessionLocal
from src.services.chat_service import _extraction_prompt


def test_extraction_prompt_includes_real_current_date():
    session = SessionLocal()
    try:
        with patch("src.services.chat_service._today", return_value=date(2026, 7, 2)):
            prompt = _extraction_prompt(session)
    finally:
        session.close()

    assert "2026-07-02" in prompt


def test_extraction_prompt_tells_model_not_to_put_dates_in_q():
    session = SessionLocal()
    try:
        prompt = _extraction_prompt(session)
    finally:
        session.close()

    assert "date_received_from" in prompt
    assert '"q"' in prompt
    # Must explicitly steer date expressions away from the free-text q field.
    lowered = prompt.lower()
    assert "do not put date" in lowered or 'not in "q"' in lowered
