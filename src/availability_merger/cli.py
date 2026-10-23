from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .calendar_export import render_ics
from .core import analyze, render_json, render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic, reviewable report from explicit JSON input."
    )
    parser.add_argument("input", type=Path, help="UTF-8 JSON input file")
    parser.add_argument("--format", choices=("markdown", "json", "ics"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--slot", action="append", type=int, help="One-based overlap number; repeat to select more."
    )
    parser.add_argument(
        "--calendar-timezone", help="Explicit UTC or fixed +/-HH:MM offset for naive overlaps."
    )
    parser.add_argument("--calendar-privacy", choices=("busy-only", "participants"))
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        report = analyze(data)
        if args.format == "ics":
            if not args.calendar_timezone or not args.calendar_privacy:
                raise ValueError("ICS export requires --calendar-timezone and --calendar-privacy")
            rendered = render_ics(
                report,
                args.slot or [],
                timezone_choice=args.calendar_timezone,
                privacy=args.calendar_privacy,
            )
        else:
            if args.slot or args.calendar_timezone or args.calendar_privacy:
                raise ValueError("calendar options require --format ics")
            rendered = render_json(report) if args.format == "json" else render_markdown(report)
        if args.output:
            if args.output.exists() or args.output.is_symlink():
                raise FileExistsError(f"output already exists: {args.output}")
            with args.output.open(
                "x", encoding="utf-8", newline="" if args.format == "ics" else None
            ) as output:
                output.write(rendered)
        else:
            binary = getattr(sys.stdout, "buffer", None) if args.format == "ics" else None
            if binary is not None:
                binary.write(rendered.encode("utf-8"))
            else:
                sys.stdout.write(rendered)
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
