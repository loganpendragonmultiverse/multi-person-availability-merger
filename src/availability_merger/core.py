from __future__ import annotations

import json
from datetime import datetime
from typing import Any

PROJECT = "multi-person-availability-merger"


def _require(data: dict[str, Any], key: str) -> Any:
    value = data.get(key)
    if value is None or value == "" or value == []:
        raise ValueError(f"{key} is required")
    return value


def _availability(data: dict[str, Any]) -> dict[str, Any]:
    people = _require(data, "people")
    required = int(data.get("minimum_people", len(people)))
    if required < 1 or required > len(people):
        raise ValueError("minimum_people is outside the participant count")
    events = []
    for person in people:
        name = str(_require(person, "name"))
        for interval in person.get("intervals", []):
            start, end = (datetime.fromisoformat(interval[0]), datetime.fromisoformat(interval[1]))
            if end <= start:
                raise ValueError("availability intervals must end after they start")
            events.extend([(start, 1, name), (end, -1, name)])
    events.sort(key=lambda item: (item[0], item[1]))
    active: set[str] = set()
    overlaps: list[dict[str, Any]] = []
    previous: datetime | None = None
    for moment, change, name in events:
        if previous is not None and moment > previous and (len(active) >= required):
            overlaps.append(
                {
                    "start": previous.isoformat(),
                    "end": moment.isoformat(),
                    "people": sorted(active),
                    "minutes": int((moment - previous).total_seconds() / 60),
                }
            )
        if change < 0:
            active.discard(name)
        else:
            active.add(name)
        previous = moment
    merged: list[dict[str, Any]] = []
    for item in overlaps:
        if (
            merged
            and merged[-1]["end"] == item["start"]
            and (merged[-1]["people"] == item["people"])
        ):
            merged[-1]["end"], merged[-1]["minutes"] = (
                item["end"],
                int(merged[-1]["minutes"]) + int(item["minutes"]),
            )
        else:
            merged.append(item)
    return {"overlaps": merged, "minimum_people": required}


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, "project": PROJECT, **_availability(data)}


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [f"# {report['project'].replace('-', ' ').title()} report", ""]
    for key, value in report.items():
        if key not in {"version", "project"}:
            lines.extend(
                [
                    f"## {key.replace('_', ' ').title()}",
                    "",
                    f"```json\n{json.dumps(value, indent=2, ensure_ascii=False, default=str)}\n```",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"
