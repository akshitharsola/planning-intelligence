"""
DHLGH national planning dataset scraper (spec section 3,
docs/superpowers/specs/2026-07-10-dhlgh-national-source-design.md). Same
shape as GalwayCountyScraper (src/sources/galway/county/scraper.py) — a
public, no-auth ArcGIS Feature Service, paginated by an incrementing
OBJECTID watermark. No files to download, so acquire() is a passthrough.

Differs from County in one respect: this feed is national (all 31 local
authorities), so discover()'s `where` clause additionally filters to
`PlanningAuthority IN (...)` from region_config['planning_authorities'],
and the query requests polygon geometry (config's `returnGeometry: true`)
since that's this source's value-add over our existing Galway sources.
"""

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.sources.base.source import BaseSource

logger = logging.getLogger(__name__)


class DHLGHScraper(BaseSource):
    def discover(self) -> list[dict]:
        url = self.region_config["arcgis_query_url"]
        watermark_field = self.region_config["watermark_field"]
        page_size = self.region_config["page_size"]
        out_fields = ",".join(self.region_config["out_fields"])
        planning_authorities = self.region_config["planning_authorities"]
        return_geometry = self.region_config.get("returnGeometry", False)
        watermark = self.region_config.get("watermark", 0)

        session = self._build_session()
        records: list[dict] = []
        current_watermark = watermark

        while True:
            page = self._query_page(
                session,
                url,
                watermark_field,
                current_watermark,
                page_size,
                out_fields,
                planning_authorities,
                return_geometry,
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
        planning_authorities: list[str],
        return_geometry: bool,
    ) -> list[dict]:
        authorities_clause = ", ".join(f"'{a}'" for a in planning_authorities)
        params = {
            "where": (
                f"{watermark_field} > {watermark} "
                f"AND PlanningAuthority IN ({authorities_clause})"
            ),
            "outFields": out_fields,
            "returnGeometry": "true" if return_geometry else "false",
            # Layer's native spatial reference is Web Mercator (wkid 102100 /
            # 3857), not WGS84 — request outSR=4326 explicitly so returned
            # ring coordinates are lat/lon degrees, matching the
            # dhlgh_applications.site_geometry column's declared SRID 4326
            # (src/core/models/dhlgh_application.py). Without this, rings
            # come back in meters and would be silently mistagged as 4326.
            "outSR": "4326",
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

        records = []
        for feature in payload.get("features", []):
            record = dict(feature["attributes"])
            if "geometry" in feature:
                record["_geometry"] = feature["geometry"]
            records.append(record)
        return records
