"""
Galway City Council weekly planning lists scraper.

Ported from duffy's scraper.py: hits the filegator REST API behind
files.galwaycity.ie directly with three plain HTTP calls
(auth -> list dir -> download). No browser automation needed.
"""

import base64
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import requests

from src.sources.base.source import BaseSource

logger = logging.getLogger(__name__)

MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


class GalwayCityScraper(BaseSource):
    def discover(self) -> list[dict]:
        lookback_months = self.region_config.get("lookback_months", 3)
        cutoff = datetime.today() - timedelta(days=lookback_months * 31)

        sess = self._auth_session()
        links: list[dict] = []
        base_url = self.region_config["base_url"]
        pdf_patterns = self.region_config["pdf_patterns"]
        known_substrings = [s for patterns in pdf_patterns.values() for s in patterns]

        for year_item in self._getdir(sess, "/"):
            if year_item["type"] != "dir" or not re.fullmatch(r"20\d{2}", year_item["name"]):
                continue
            year = int(year_item["name"])

            for month_item in self._getdir(sess, year_item["path"]):
                if month_item["type"] != "dir":
                    continue
                mk = month_item["name"].strip().lower().split()[0]
                if mk not in MONTH_NAMES:
                    continue
                month_num = MONTH_NAMES[mk]
                if datetime(year, month_num, 1) < cutoff:
                    continue
                month_display = mk.capitalize()

                for week_item in self._getdir(sess, month_item["path"]):
                    if week_item["type"] != "dir":
                        continue
                    week_range = self._normalise_week(week_item["name"])

                    for file_item in self._getdir(sess, week_item["path"]):
                        if file_item["type"] != "file":
                            continue
                        filename = file_item["name"]
                        if not filename.lower().endswith(".pdf"):
                            continue
                        if not any(s in filename.lower() for s in known_substrings):
                            continue
                        links.append({
                            "url": self._make_dl_url(base_url, file_item["path"]),
                            "filename": filename,
                            "year": year,
                            "month_num": month_num,
                            "month_name": month_display,
                            "week_range": week_range,
                        })
        return links

    def acquire(self, items: list[dict]) -> list[Path]:
        sess = self._auth_session()
        saved: list[Path] = []
        for link in items:
            local_path = self._build_local_path(link)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            r = sess.get(link["url"], timeout=60)
            r.raise_for_status()
            if r.content[:4] == b"%PDF":
                local_path.write_bytes(r.content)
                saved.append(local_path)
            else:
                logger.error(f"Response for {link['filename']} is not a PDF")
        return saved

    def _build_local_path(self, link: dict) -> Path:
        return (
            self.temp_dir
            / str(link["year"])
            / link["month_name"]
            / link["week_range"]
            / link["filename"]
        )

    def _auth_session(self) -> requests.Session:
        base_url = self.region_config["base_url"]
        sess = requests.Session()
        sess.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": base_url,
        })
        r = sess.get(base_url + "?r=/getuser", timeout=20)
        r.raise_for_status()
        token = r.headers.get("X-CSRF-Token") or r.headers.get("x-csrf-token")
        if not token:
            raise ValueError("No CSRF token in /getuser response — API may have changed.")
        sess.headers["x-csrf-token"] = token
        sess.headers["Content-Type"] = "application/json"
        return sess

    def _getdir(self, sess: requests.Session, path: str) -> list[dict]:
        base_url = self.region_config["base_url"]
        r = sess.post(base_url + "?r=/getdir", json={"dir": path}, timeout=20)
        r.raise_for_status()
        return [f for f in r.json()["data"]["files"] if f["type"] != "back"]

    @staticmethod
    def _make_dl_url(base_url: str, file_path: str) -> str:
        b64 = base64.b64encode(file_path.encode()).decode()
        return base_url + "?r=/download&path=" + quote(b64, safe="")

    @staticmethod
    def _normalise_week(server_name: str) -> str:
        s = server_name.strip()
        m = re.match(
            r"(\d{2})\.(\d{2})\.(\d{4})\s*(?:-+|to)\s*(\d{2})\.(\d{2})\.(\d{4})",
            s, re.IGNORECASE
        )
        if m:
            return f"{int(m.group(1))}-{int(m.group(4))}"
        return s
