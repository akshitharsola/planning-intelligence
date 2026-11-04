"""County document fetcher for Galway County Council decision notices and ePlanning condition counts."""

from dataclasses import dataclass
import http.cookiejar
import logging
import re
import time
from typing import Any, Callable, Optional
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "planning-intelligence (contact harsolaakshit@gmail.com)"
BASE_DOCS_URL = "https://apps.galwaycoco.ie/ViewExternalDocuments"
EPLAN_URL_TEMPLATE = "https://www.eplanning.ie/GalwayCC/AppFileRefDetails/{}/0"

WANTED_DOC_TYPES = {
    "notification of decision": "notification_of_decision",
    "final grant": "final_grant",
}


@dataclass(frozen=True)
class DocLink:
    council_doc_id: str
    doc_type: str
    url: str


def list_decision_docs(html: str, ref: str) -> list[DocLink]:
    """Parse document viewer HTML table and extract decision document links.

    Filters to notification_of_decision and final_grant only.
    """
    clean_ref = ref.replace("/", "")
    docs: list[DocLink] = []

    # Look for table rows containing links to ViewPDF.aspx
    for row_match in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        row_content = row_match.group(1)
        href_match = re.search(r"href=['\"](ViewPDF\.aspx\?[^'\"]+)", row_content, re.I)
        if not href_match:
            continue

        raw_href = href_match.group(1).replace("&amp;", "&")

        # Extract anchor link text / cell label
        label_match = re.search(r"<a[^>]*>(.*?)</a>", row_content, re.S | re.I)
        if label_match:
            raw_label = re.sub(r"<[^>]+>", " ", label_match.group(1))
        else:
            raw_label = re.sub(r"<[^>]+>", " ", row_content)

        clean_label = re.sub(r"\s+", " ", raw_label).strip()
        # Remove leading doc id digits from label, e.g. "2733957 Notification of Decision" -> "Notification of Decision"
        doc_type_text = re.sub(r"^\d+\s+", "", clean_label).strip().lower().replace("_", " ")

        doc_type_key = None
        for want_label, normalized_key in WANTED_DOC_TYPES.items():
            if want_label in doc_type_text:
                doc_type_key = normalized_key
                break

        if not doc_type_key:
            continue

        # Extract council document id from href parameter ref=<DocID>
        doc_id_match = re.search(r"[?&]ref=([^&'\"]+)", raw_href, re.I)
        if not doc_id_match:
            continue
        council_doc_id = doc_id_match.group(1)

        doc_url = f"{BASE_DOCS_URL}/ViewPDF.aspx?RefNo={clean_ref}&ViewFind=true&ref={council_doc_id}"
        docs.append(
            DocLink(
                council_doc_id=council_doc_id,
                doc_type=doc_type_key,
                url=doc_url,
            )
        )

    return docs


class CountyDocFetcher:
    """Polite fetcher for Galway County Council decision notices and ePlanning details."""

    def __init__(
        self,
        min_interval: float = 1.0,
        user_agent: str = DEFAULT_USER_AGENT,
        opener: Any = None,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        self.min_interval = min_interval
        self.user_agent = user_agent
        self.clock = clock
        self.sleep = sleep
        self.timeout = timeout
        self.max_retries = max_retries
        self._last_request_time: float = 0.0

        if opener is not None:
            self._opener = opener
        else:
            cookie_jar = http.cookiejar.CookieJar()
            self._opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(cookie_jar)
            )

    def _rate_limit(self) -> None:
        now = self.clock()
        elapsed = now - self._last_request_time
        if elapsed < self.min_interval and self._last_request_time > 0.0:
            wait_time = self.min_interval - elapsed
            self.sleep(wait_time)
        self._last_request_time = self.clock()

    def _get(self, url: str, referer: Optional[str] = None) -> Optional[bytes]:
        headers = {"User-Agent": self.user_agent}
        if referer:
            headers["Referer"] = referer

        req = urllib.request.Request(url, headers=headers)
        attempt = 0
        while attempt <= self.max_retries:
            self._rate_limit()
            try:
                with self._opener.open(req, timeout=self.timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):
                    logger.error("HTTP %d received for %s - stopping immediately", e.code, url)
                    raise RuntimeError(f"HTTP {e.code} received from council server: aborting run") from e
                attempt += 1
                if attempt > self.max_retries:
                    logger.warning("HTTP fetch failed after %d attempts for %s: %s", attempt, url, e)
                    return None
                backoff = 0.5 * (2 ** (attempt - 1))
                self.sleep(backoff)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                attempt += 1
                if attempt > self.max_retries:
                    logger.warning("HTTP fetch failed after %d attempts for %s: %s", attempt, url, e)
                    return None
                backoff = 0.5 * (2 ** (attempt - 1))
                self.sleep(backoff)
            except Exception as e:
                logger.error("Unexpected error fetching %s: %s", url, e)
                return None
        return None

    def fetch_list(self, ref: str) -> str:
        """Fetch the HTML document list page for an application ref."""
        clean_ref = ref.replace("/", "")
        url = f"{BASE_DOCS_URL}/?RefNo={clean_ref}"
        data = self._get(url)
        if not data:
            return ""
        return data.decode("utf-8", "replace")

    def fetch_pdf(self, link: DocLink) -> Optional[bytes]:
        """Fetch PDF bytes for a DocLink. Returns None if body does not start with %PDF."""
        # Parse ref from url to send as Referer
        ref_match = re.search(r"RefNo=([^&]+)", link.url)
        referer = f"{BASE_DOCS_URL}/?RefNo={ref_match.group(1)}" if ref_match else BASE_DOCS_URL
        data = self._get(link.url, referer=referer)
        if not data or not data.startswith(b"%PDF"):
            return None
        return data

    def fetch_eplanning_condition_count(self, ref: str) -> Optional[int]:
        """Fetch condition count stated on ePlanning summary page."""
        clean_ref = ref.replace("/", "")
        url = EPLAN_URL_TEMPLATE.format(clean_ref)
        data = self._get(url)
        if not data:
            return None
        text = data.decode("utf-8", "replace")
        cleaned_text = re.sub(r"<[^>]+>|\s+", " ", text)
        m = re.search(r"Number of Conditions:\s*(\d+)", cleaned_text, re.I)
        return int(m.group(1)) if m else None


def fetch_eplanning_condition_count(ref: str, fetcher: Optional[CountyDocFetcher] = None) -> Optional[int]:
    """Convenience helper to fetch ePlanning condition count."""
    active_fetcher = fetcher or CountyDocFetcher()
    return active_fetcher.fetch_eplanning_condition_count(ref)
