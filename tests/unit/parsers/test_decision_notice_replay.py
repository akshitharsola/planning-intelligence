import collections
import csv
import glob
from pathlib import Path
import subprocess
import pytest

from src.parsers.decision_notice.extractor import parse_notice

SPIKE_DIR = Path(
    "/private/tmp/claude-501/-Users-akshitharsola-Documents-AiAgentic/6df0c992-c82b-4cdc-b4d0-d1ca911e909c/scratchpad/poc"
)
PDFS_COUNTY = SPIKE_DIR / "pdfs_county"


@pytest.mark.skipif(not PDFS_COUNTY.exists(), reason="Spike County PDFs not present")
def test_replay_all_172_spike_county_pdfs():
    csv1 = SPIKE_DIR / "results_county.csv"
    csv2 = SPIKE_DIR / "results_county2.csv"
    assert csv1.exists() and csv2.exists()

    with open(csv1, mode="r", encoding="utf-8") as f:
        m1 = {r["ref"]: r for r in csv.DictReader(f)}
    with open(csv2, mode="r", encoding="utf-8") as f:
        m2 = {r["ref"]: r for r in csv.DictReader(f)}
    meta = {**m1, **m2}

    pdf_files = sorted(glob.glob(str(PDFS_COUNTY / "*.pdf")))
    assert len(pdf_files) == 172

    counts = collections.Counter()
    for pdf_path in pdf_files:
        fname = Path(pdf_path).name
        ref = fname.split("_")[0]
        app_meta = meta.get(ref, {})
        eplan_count = int(app_meta["eplan_conditions"]) if app_meta.get("eplan_conditions") else None
        decision = app_meta.get("decision")

        res = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            capture_output=True,
            text=True,
            check=True,
        )
        raw_text = res.stdout

        parsed = parse_notice(
            raw_text,
            authority="Galway County Council",
            eplan_count=eplan_count,
            decision=decision,
        )
        counts[parsed.status] += 1

    assert counts["validated"] == 155
    assert counts["count_mismatch"] == 3
    assert counts["needs_ocr"] + counts["no_schedule"] == 14

