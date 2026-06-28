"""
Galway County Council weekly planning lists scraper — built fresh, no
duffy precedent (spec section 5.2). The weekly-list page is plain HTML
with PDF download links, unlike Galway City's filegator REST API.
"""

import logging
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.sources.base.source import BaseSource

logger = logging.getLogger(__name__)


class GalwayCountyScraper(BaseSource):
    def discover(self) -> list[dict]:
        url = self.region_config["weekly_list_url"]
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return self._parse_pdf_links(resp.text, base_url=url)

    def acquire(self, items: list[dict]) -> list[Path]:
        saved: list[Path] = []
        for link in items:
            local_path = Path(self.temp_dir) / link["filename"]
            local_path.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(link["url"], timeout=60)
            r.raise_for_status()
            if r.content[:4] == b"%PDF":
                local_path.write_bytes(r.content)
                saved.append(local_path)
            else:
                logger.error(f"Response for {link['filename']} is not a PDF")
        return saved

    def _parse_pdf_links(self, html: str, base_url: str | None = None) -> list[dict]:
        base_url = base_url or self.region_config["weekly_list_url"]
        soup = BeautifulSoup(html, "html.parser")
        links: list[dict] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.lower().endswith(".pdf"):
                continue
            full_url = urljoin(base_url, href)
            filename = href.rsplit("/", 1)[-1]
            links.append({"url": full_url, "filename": filename})
        return links
