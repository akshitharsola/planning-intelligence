from src.core.db.session import SessionLocal
from src.core.ingestion_state import (
    get_watermark,
    set_watermark,
    is_file_ingested,
    mark_file_ingested,
)


def test_get_watermark_returns_none_when_unset():
    session = SessionLocal()
    try:
        assert get_watermark(session, "test_region_watermark_unset") is None
    finally:
        session.rollback()
        session.close()


def test_set_then_get_watermark_roundtrips():
    session = SessionLocal()
    try:
        set_watermark(session, "test_region_watermark_roundtrip", "12345")
        session.commit()
        assert get_watermark(session, "test_region_watermark_roundtrip") == "12345"
    finally:
        session.execute(
            __import__("sqlalchemy").text(
                "DELETE FROM ingestion_state WHERE region = 'test_region_watermark_roundtrip'"
            )
        )
        session.commit()
        session.close()


def test_set_watermark_twice_updates_value():
    session = SessionLocal()
    try:
        set_watermark(session, "test_region_watermark_update", "1")
        session.commit()
        set_watermark(session, "test_region_watermark_update", "2")
        session.commit()
        assert get_watermark(session, "test_region_watermark_update") == "2"
    finally:
        session.execute(
            __import__("sqlalchemy").text(
                "DELETE FROM ingestion_state WHERE region = 'test_region_watermark_update'"
            )
        )
        session.commit()
        session.close()


def test_is_file_ingested_false_when_unset():
    session = SessionLocal()
    try:
        assert is_file_ingested(session, "test_region_file_unset", "file_a.pdf") is False
    finally:
        session.rollback()
        session.close()


def test_mark_then_is_file_ingested_roundtrips():
    session = SessionLocal()
    try:
        mark_file_ingested(session, "test_region_file_roundtrip", "file_a.pdf")
        session.commit()
        assert is_file_ingested(session, "test_region_file_roundtrip", "file_a.pdf") is True
        assert is_file_ingested(session, "test_region_file_roundtrip", "file_b.pdf") is False
    finally:
        session.execute(
            __import__("sqlalchemy").text(
                "DELETE FROM ingested_files WHERE region = 'test_region_file_roundtrip'"
            )
        )
        session.commit()
        session.close()
