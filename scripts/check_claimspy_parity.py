"""Check private ClaimSpy cohort output without redistributing its sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tex2markdown import PaperMetadata, convert


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claimspy-root", type=Path, required=True)
    parser.add_argument("--run", default="retrieval_v135")
    parser.add_argument("--conversion-date", default="July 16, 2026")
    return parser.parse_args()


def paper_metadata(row: dict) -> PaperMetadata:
    values = {name: row.get(name) for name in PaperMetadata.__dataclass_fields__}
    return PaperMetadata(**values)


def main() -> None:
    args = parse_args()
    run = args.claimspy_root / "retrieval_markdown_processing/runs" / args.run
    mismatches = []
    count = 0
    with (run / "papers.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            source = (args.claimspy_root / row["source_path"]).read_text(encoding="utf-8")
            actual = convert(source, filename=row["source_file"], metadata=paper_metadata(row),
                             conversion_date=args.conversion_date).markdown.encode()
            expected = (args.claimspy_root / row["document_path"]).read_bytes()
            count += 1
            if actual != expected:
                mismatches.append(row["id"])
    print(json.dumps({"papers": count, "byte_identical": count - len(mismatches),
                      "mismatches": mismatches}))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
