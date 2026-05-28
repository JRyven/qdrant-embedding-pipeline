"""Sanity checks for NDJSON produced by the ingest pipeline.

Usage:
  python -m src.tagging.sanity --ndjson path/to/ingest.ndjson --report out.json

Outputs a JSON report with record counts, sample texts, and simple PII detections.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Dict, Any


EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s()]{6,}\d)")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def scan_record(text: str) -> Dict[str, Any]:
    hits = {}
    emails = EMAIL_RE.findall(text)
    if emails:
        hits["emails"] = emails[:5]
    phones = PHONE_RE.findall(text)
    if phones:
        hits["phones"] = phones[:5]
    ssns = SSN_RE.findall(text)
    if ssns:
        hits["ssns"] = ssns[:5]
    return hits


def run(ndjson_path: Path, report_path: Path) -> None:
    total = 0
    samples = []
    pii_findings = []

    with ndjson_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            text = obj.get("text", "")
            if len(samples) < 5:
                samples.append({"id": obj.get("id"), "source_path": obj.get("source_path"), "snippet": text[:200]})
            hits = scan_record(text)
            if hits:
                pii_findings.append({"id": obj.get("id"), "source_path": obj.get("source_path"), "hits": hits})

    report = {
        "total_records": total,
        "sample_records": samples,
        "pii_findings_count": len(pii_findings),
        "pii_findings": pii_findings[:20],
    }

    with report_path.open("w", encoding="utf-8") as outf:
        json.dump(report, outf, indent=2)


def main(argv=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ndjson", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args(argv)
    ndjson_path = Path(args.ndjson)
    report_path = Path(args.report)
    if not ndjson_path.exists():
        raise SystemExit(f"NDJSON input not found: {ndjson_path}")
    run(ndjson_path, report_path)


if __name__ == "__main__":
    main()
