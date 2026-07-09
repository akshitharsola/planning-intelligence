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
            client = FakeLLMClient(replies=['{"q": "chattestville"}'])
            result = answer_question(session, "What's new in Chattestville?", client=client)
        finally:
            session.close()

        assert result["total"] == 1
        assert result["applications"][0].application_ref == f"{PREFIX}/0001"
        assert result["filters"] == {"q": "chattestville"}
        assert f"{PREFIX}/0001" in result["answer"]
        assert len(client.calls) == 1
    finally:
        _cleanup()


def test_answer_question_unfiltered_search_when_llm_extracts_no_filters():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            # LLM reachable, but genuinely finds no confident filters for a vague
            # question -> a real (if broad) unfiltered search is the correct,
            # intentional result, NOT the "unavailable" outage message.
            client = FakeLLMClient(replies=["{}"])
            result = answer_question(session, "Show me everything", client=client)
        finally:
            session.close()

        assert result["filters"] == {}
        assert result["total"] >= 1
        assert "Found" in result["answer"]
    finally:
        _cleanup()


def test_answer_question_reports_unavailable_when_llm_unreachable():
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

        # Filter extraction failed (LLM unreachable) -> must NOT silently fall
        # back to an unfiltered search of the whole table. Report the outage
        # explicitly instead.
        assert result["total"] == 0
        assert result["filters"] == {}
        assert result["applications"] == []
        assert "unavailable" in result["answer"].lower()
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
        assert "Galway City and County" in result["answer"]
        # summarize() must short-circuit on zero results without a second LLM call
        assert len(client.calls) == 1
    finally:
        _cleanup()


def test_answer_question_distinguishes_narrowed_filters_from_out_of_coverage():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            # The seeded row is in Chattestville with status "Granted" -- asking
            # for "Refused" ones returns zero rows, but Chattestville itself IS
            # covered, so the answer must NOT claim the place is out of pilot
            # coverage (that was the bug: a real place + a too-narrow status/date
            # filter produced the same generic "not in this dataset" message as
            # a genuinely unsupported place like Dublin).
            client = FakeLLMClient(
                replies=['{"planning_status_current": "Refused", "q": "chattestville"}']
            )
            result = answer_question(session, "Rejected applications in Chattestville", client=client)
        finally:
            session.close()

        assert result["total"] == 0
        assert "Galway City and County" not in result["answer"]
        assert "combination of filters" in result["answer"]
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
                ]
            )
            result = answer_question(session, "What's new in Chattestville?", client=client)
        finally:
            session.close()

        assert result["filters"] == {"q": "chattestville"}
        assert result["total"] == 1
    finally:
        _cleanup()


def test_answer_question_drops_hallucinated_application_type():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(
                replies=['{"application_type": "NOTREALTYPE", "q": "chattestville"}']
            )
            result = answer_question(session, "What's new in Chattestville?", client=client)
        finally:
            session.close()

        # "NOTREALTYPE" is not a real application_type in this dataset -> must be
        # dropped, not applied as a filter, so the real (Permission-typed) row
        # still matches.
        assert "application_type" not in result["filters"]
        assert result["total"] == 1
        assert result["applications"][0].application_ref == f"{PREFIX}/0001"
    finally:
        _cleanup()


def test_answer_question_keeps_valid_application_type():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(
                replies=['{"application_type": "Permission", "q": "chattestville"}']
            )
            result = answer_question(session, "What's new in Chattestville?", client=client)
        finally:
            session.close()

        # "Permission" IS a real application_type in this dataset -> must be kept.
        assert result["filters"]["application_type"] == "Permission"
        assert result["total"] == 1
    finally:
        _cleanup()


def test_answer_question_drops_status_guess_when_question_names_an_application_ref():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            # The question only asks for a ref's status, it doesn't state one --
            # a status guess here is exactly the pattern observed to hallucinate
            # in the wild, so it must be dropped even though "Granted" is a real
            # allowed value (the enum check alone wouldn't catch this).
            client = FakeLLMClient(
                replies=['{"planning_status_current": "Granted", "q": "26/20"}']
            )
            result = answer_question(session, "What's the status of application 26/20?", client=client)
        finally:
            session.close()

        assert "planning_status_current" not in result["filters"]
        assert result["filters"]["q"] == "26/20"
    finally:
        _cleanup()


def test_answer_question_drops_authority_guessed_from_place_name_alone():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            # Live testing found qwen2.5:3b silently guessing "Galway City
            # Council" from a place name like "Tuam" even though the prompt
            # says never to do that -- the guess is a REAL enum value so the
            # enum check alone doesn't catch it, and it silently drops ~99% of
            # true matches (549 rows -> 1) with no error, no "no match"
            # message. The question below never names a council explicitly.
            client = FakeLLMClient(
                replies=[
                    '{"planning_authority": "Galway City Council", '
                    '"planning_status_current": "Granted", "q": "chattestville"}'
                ]
            )
            result = answer_question(session, "Show granted applications in Chattestville", client=client)
        finally:
            session.close()

        assert "planning_authority" not in result["filters"]
        assert result["filters"]["q"] == "chattestville"
        assert result["total"] == 1
    finally:
        _cleanup()


def test_answer_question_keeps_authority_when_question_names_it_explicitly():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(
                replies=[
                    '{"planning_authority": "Galway City Council", "q": "chattestville"}'
                ]
            )
            result = answer_question(
                session,
                "Show applications in Chattestville from Galway City Council",
                client=client,
            )
        finally:
            session.close()

        assert result["filters"]["planning_authority"] == "Galway City Council"
        assert result["total"] == 1
    finally:
        _cleanup()


def test_answer_question_drops_hallucinated_planning_status():
    _cleanup()
    _seed()
    try:
        session = SessionLocal()
        try:
            client = FakeLLMClient(
                replies=['{"planning_status_current": "Unknown", "q": "chattestville"}']
            )
            result = answer_question(session, "What's the status in Chattestville?", client=client)
        finally:
            session.close()

        # "Unknown" is not a real planning_status_current value in this dataset ->
        # must be dropped, not applied as a filter, so the real (Granted-status)
        # row still matches.
        assert "planning_status_current" not in result["filters"]
        assert result["total"] == 1
        assert result["applications"][0].application_ref == f"{PREFIX}/0001"
    finally:
        _cleanup()
