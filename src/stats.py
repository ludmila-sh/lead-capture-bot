"""Local funnel report from the interaction log.

Reads the JSONL written by src.events (no Google auth, works offline) and
prints per-segment counts for the Phase 4 milestones. The client normally
reads the Google Sheet instead; this is for local checks.

    python -m src.stats            # table
    python -m src.stats --csv      # CSV to stdout
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from src.config import settings

EVENTS = ("start", "magnet_delivered", "handoff")


def collect(path: Path) -> dict[str, dict[str, object]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {e: 0 for e in EVENTS})
    users: dict[str, set[object]] = defaultdict(set)

    if not path.is_file():
        return {}

    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            event = record.get("event")
            if event not in EVENTS:
                continue
            segment = record.get("segment") or "none"
            counts[segment][event] += 1
            if record.get("user_id") is not None:
                users[segment].add(record["user_id"])
                users["*"].add(record["user_id"])

    if not counts:
        return {}
    report: dict[str, dict[str, object]] = {
        segment: {**counts[segment], "unique_users": len(users[segment])}
        for segment in sorted(counts)
    }
    # Reserved key: distinct users across all segments (not the column sum).
    report["*"] = {**{e: 0 for e in EVENTS}, "unique_users": len(users["*"])}
    return report


def _rows(report: dict[str, dict[str, object]]) -> list[list[object]]:
    header = ["segment", *EVENTS, "unique_users"]
    rows = [header]
    totals = {e: 0 for e in EVENTS}
    for segment, data in report.items():
        if segment == "*":
            continue
        rows.append([segment, *(data[e] for e in EVENTS), data["unique_users"]])
        for e in EVENTS:
            totals[e] += data[e]
    overall_users = report.get("*", {}).get("unique_users", 0)
    rows.append(["TOTAL", *(totals[e] for e in EVENTS), overall_users])
    return rows


def print_table(report: dict[str, dict[str, object]]) -> None:
    rows = _rows(report)
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for idx, row in enumerate(rows):
        line = "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        print(line)
        if idx == 0:
            print("  ".join("-" * w for w in widths))


def print_csv(report: dict[str, dict[str, object]]) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerows(_rows(report))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", action="store_true", help="write CSV to stdout")
    parser.add_argument(
        "--log",
        default=settings.interaction_log_path,
        help="path to the interaction JSONL (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    report = collect(Path(args.log))
    if not report:
        print(f"no events in {args.log}", file=sys.stderr)
        return
    (print_csv if args.csv else print_table)(report)


if __name__ == "__main__":
    main()
