"""
Galway County Council planning register scraper — built fresh, no duffy
precedent (spec section 5.2). Source is the council's public ArcGIS Feature
Service (no auth required), not a PDF weekly list: galwaycoco.ie redirects
to galway.ie and isn't directly scrapable, and eplanning.ie's HTML table
was assessed as too fragile. The ArcGIS endpoint returns structured JSON
records directly, paginated via an incrementing OBJECTID watermark, so
there are no files to download — discover() does the full fetch and
acquire() is a passthrough to satisfy the BaseSource contract.
"""

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.sources.base.source import BaseSource

logger = logging.getLogger(__name__)


class GalwayCountyScraper(BaseSource):
    def discover(self) -> list[dict]:
        url = self.region_config["arcgis_query_url"]
        watermark_field = self.region_config["watermark_field"]
        page_size = self.region_config["page_size"]
        out_fields = ",".join(self.region_config["out_fields"])
        watermark = self.region_config.get("watermark", 0)

        session = self._build_session()
        records: list[dict] = []
        current_watermark = watermark

        while True:
            page = self._query_page(
                session, url, watermark_field, current_watermark, page_size, out_fields
            )
            if not page:
                break
            records.extend(page)
            current_watermark = page[-1][watermark_field]
            if len(page) < page_size:
                break

        session.close()
        return records

    def acquire(self, items: list[dict]) -> list[dict]:
        return items

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    @staticmethod
    def _query_page(
        session: requests.Session,
        url: str,
        watermark_field: str,
        watermark: int,
        page_size: int,
        out_fields: str,
    ) -> list[dict]:
        params = {
            "where": f"{watermark_field} > {watermark}",
            "outFields": out_fields,
            "returnGeometry": "false",
            "orderByFields": f"{watermark_field} ASC",
            "resultRecordCount": page_size,
            "f": "json",
        }
        resp = session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        if "error" in payload:
            raise RuntimeError(
                f"ArcGIS API error {payload['error'].get('code')}: "
                f"{payload['error'].get('message')}"
            )

        return [f["attributes"] for f in payload.get("features", [])]
