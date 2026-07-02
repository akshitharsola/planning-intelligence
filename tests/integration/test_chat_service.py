from datetime import date, datetime

from sqlalchemy import text

from src.core.db.session import SessionLocal
from src.services.chat_service import answer_question

PREFIX = "CHATTEST"


class FakeLLMClient:
    """Scripted client: returns queued replies in order, one per .chat() call."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def chat(self, system, user):
        self.calls.append((system, user))
        return self.replies.pop(0)


class RaisingLLMClient:
    def chat(self, system, user):
        raise RuntimeError("model unreachable")


def _cleanup():
    session = SessionLocal()
    try:
        session.execute(
            text("DELETE FROM application_events WHERE application_ref LIKE :p"),
            {"p": f"{PREFIX}/%"},
        )
        session.execute(
            text("DELETE FROM applications WHERE application_ref LIKE :p"),
            {"p": f"{PREFIX}/%"},
        )
        session.commit()
    finally:
        session.close()


def _seed():
    session = SessionLocal()
    try:
        session.execute(
            text(
                """
                INSERT INTO applications (
                    id, planning_authority, source_entity, application_ref,
                    applicant_name, site_address, development_description,
                    application_type, planning_status_current, date_received,
                    source_system, source_file, source_ingested_at,
                    further_information_flag, protected_structure_flag,
                    eia_eis_flag, other_regulatory_flags, commuter_belt_flag,
                    raw_payload_json
                ) VALUES (
                    gen_random_uuid(), 'Galway City Council', 'GALWAY_CITY_COUNCIL',
                    :ref, 'Jane Example', 'Main Street, Chattestville', 'New dwelling',
                    'Permission', 'Granted', :received,
                    'TEST', 'test.pdf', :ingested_at,
                    false, false, false, '{}', false, '{}'
                )
                """
            ),
            {
                "ref": f"{PREFIX}/0001",
                "received": date(2026, 3, 1),
                "ingested_at": datetime(2026, 3, 2, 9, 0),
            },
        )
        session.commit()
    finally:
        session.close()


def test_answer_question_extracts_filters_and_summarizes():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(
                replies=[
                    '{"q": "chattestville"}',
                    "There is one new dwelling permission granted in Chattestville.",
                ]
            )
            result = answer_question(session, "What's new in Chattestville?", client=client)
        finally:
            session.close()

        assert result["total"] == 1
        assert result["applications"][0].application_ref == f"{PREFIX}/0001"
        assert result["filters"] == {"q": "chattestville"}
        assert "Chattestville" in result["answer"]
        assert len(client.calls) == 2
    finally:
        _cleanup()


def test_answer_question_falls_back_when_llm_unreachable():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            result = answer_question(
                session, "What's new in Chattestville?", client=RaisingLLMClient()
            )
        finally:
            session.close()

        # No filters extracted (LLM unreachable) -> unfiltered search, but the
        # fallback summary must still be produced without raising.
        assert result["total"] >= 1
        assert isinstance(result["answer"], str)
        assert result["answer"]
    finally:
        _cleanup()


def test_answer_question_no_matches_returns_no_match_message():
    _cleanup()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(replies=['{"q": "nonexistentplace"}'])
            result = answer_question(session, "Anything in Nonexistentplace?", client=client)
        finally:
            session.close()

        assert result["total"] == 0
        assert result["answer"] == "No applications matched your question."
        # summarize() must short-circuit on zero results without a second LLM call
        assert len(client.calls) == 1
    finally:
        _cleanup()


def test_answer_question_ignores_unknown_filter_keys_from_llm():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(
                replies=[
                    '{"q": "chattestville", "delete_all": true, "sql": "DROP TABLE applications"}',
                    "One match found.",
                ]
            )
            result = answer_question(session, "What's new in Chattestville?", client=client)
        finally:
            session.close()

        assert result["filters"] == {"q": "chattestville"}
        assert result["total"] == 1
    finally:
        _cleanup()
