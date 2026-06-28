from src.sources.galway.county.scraper import GalwayCountyScraper

SAMPLE_HTML = """
<html><body>
  <div class="weekly-list">
    <a href="/files/weekly-2026-03-02-received.pdf">Applications Received 2-6 March 2026</a>
    <a href="/files/weekly-2026-03-02-granted.pdf">Applications Granted 2-6 March 2026</a>
    <a href="/about">About this page</a>
  </div>
</body></html>
"""


def test_parse_pdf_links_filters_to_pdfs_only():
    config = {"weekly_list_url": "https://www.galwaycoco.ie/planning/weekly-lists/"}
    scraper = GalwayCountyScraper(region_config=config, temp_dir="/tmp/unused")
    links = scraper._parse_pdf_links(SAMPLE_HTML)
    assert len(links) == 2
    assert links[0]["filename"] == "weekly-2026-03-02-received.pdf"
    assert links[0]["url"] == "https://www.galwaycoco.ie/files/weekly-2026-03-02-received.pdf"
