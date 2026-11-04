from pathlib import Path
import pytest

from src.sources.galway.decision_documents import (
    CountyDocFetcher,
    DocLink,
    fetch_eplanning_condition_count,
    list_decision_docs,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


def read_fixture(name: str) -> str:
    path = FIXTURES_DIR / name
    return path.read_text(encoding="utf-8")


def test_list_decision_docs_filters_types():
    html = read_fixture("galway_county_doc_list.html")
    docs = list_decision_docs(html, ref="26136")

    # In galway_county_doc_list.html:
    # 2734008 Planners Report (ignored)
    # 2733957 Notification of Decision (included)
    # 2719430 Extension of Appropriate Period Application Form (ignored)
    assert len(docs) == 1
    doc = docs[0]
    assert doc.council_doc_id == "2733957"
    assert doc.doc_type == "notification_of_decision"
    assert doc.url == "https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=26136&ViewFind=true&ref=2733957"


def test_list_decision_docs_final_grant():
    html = """
    <table>
      <tr>
        <td><a href="ViewPDF.aspx?RefNo=2260277&amp;ViewFind=true&amp;ref=2378606">2378606 Final Grant</a></td>
      </tr>
      <tr>
        <td><a href="ViewPDF.aspx?RefNo=2260277&amp;ViewFind=true&amp;ref=2360000">2360000 Notification of Decision</a></td>
      </tr>
    </table>
    """
    docs = list_decision_docs(html, ref="2260277")
    assert len(docs) == 2
    types = {d.doc_type for d in docs}
    assert types == {"final_grant", "notification_of_decision"}


def test_fetch_pdf_rejects_html():
    class FakeOpener:
        def __init__(self, content: bytes):
            self.content = content

        def open(self, req, timeout=None):
            class FakeResp:
                def __init__(self, data):
                    self.data = data
                    self.headers = {"Content-Type": "text/html"}

                def read(self):
                    return self.data

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return FakeResp(self.content)

    fake_html_content = b"<html><body>Access Denied or Viewer Error</body></html>"
    fetcher = CountyDocFetcher(opener=FakeOpener(fake_html_content))
    link = DocLink(
        council_doc_id="123",
        doc_type="notification_of_decision",
        url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=26136&ViewFind=true&ref=123",
    )
    result = fetcher.fetch_pdf(link)
    assert result is None


def test_fetch_pdf_accepts_valid_pdf():
    class FakeOpener:
        def open(self, req, timeout=None):
            class FakeResp:
                def read(self):
                    return b"%PDF-1.5 test pdf content"

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return FakeResp()

    fetcher = CountyDocFetcher(opener=FakeOpener())
    link = DocLink(
        council_doc_id="123",
        doc_type="notification_of_decision",
        url="https://apps.galwaycoco.ie/ViewExternalDocuments/ViewPDF.aspx?RefNo=26136&ViewFind=true&ref=123",
    )
    result = fetcher.fetch_pdf(link)
    assert result is not None
    assert result.startswith(b"%PDF")


def test_rate_limiter_spaces_requests():
    current_time = [100.0]
    sleep_calls = []

    def fake_clock():
        return current_time[0]

    def fake_sleep(duration):
        sleep_calls.append(duration)
        current_time[0] += duration

    class FakeOpener:
        def open(self, req, timeout=None):
            class FakeResp:
                def read(self):
                    return b"<html>dummy</html>"

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return FakeResp()

    fetcher = CountyDocFetcher(
        min_interval=1.0,
        opener=FakeOpener(),
        clock=fake_clock,
        sleep=fake_sleep,
    )

    # First request: no sleep needed
    fetcher.fetch_list("26136")
    assert len(sleep_calls) == 0

    # Advance clock only 0.2s before second request
    current_time[0] += 0.2
    fetcher.fetch_list("26137")
    assert len(sleep_calls) == 1
    assert pytest.approx(sleep_calls[0], 0.01) == 0.8

    # Advance clock 0.5s before third request
    current_time[0] += 0.5
    fetcher.fetch_list("26138")
    assert len(sleep_calls) == 2
    assert pytest.approx(sleep_calls[1], 0.01) == 0.5


def test_condition_count_regex():
    html_with_count = "<div>Some text</div><div>Number of Conditions: 17</div>"
    class FakeOpener:
        def open(self, req, timeout=None):
            class FakeResp:
                def read(self):
                    return html_with_count.encode("utf-8")

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return FakeResp()

    fetcher = CountyDocFetcher(opener=FakeOpener())
    count = fetcher.fetch_eplanning_condition_count("2260277")
    assert count == 17

    html_no_count = "<div>Some text without condition count</div>"
    class FakeOpenerNoCount:
        def open(self, req, timeout=None):
            class FakeResp:
                def read(self):
                    return html_no_count.encode("utf-8")

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return FakeResp()

    fetcher_no_count = CountyDocFetcher(opener=FakeOpenerNoCount())
    assert fetcher_no_count.fetch_eplanning_condition_count("2260277") is None

