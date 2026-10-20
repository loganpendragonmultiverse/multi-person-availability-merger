from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

PROJECT = "multi-person-availability-merger"


def _require(data: dict[str, Any], key: str) -> Any:
    if not isinstance(data, dict):
        raise TypeError("input and participant records must be JSON objects")
    value = data.get(key)
    if value is None or value == "" or value == []:
        raise ValueError(f"{key} is required")
    return value


def _datetime(value: str) -> datetime:
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:\d{2})?",
        value,
    ):
        raise ValueError("interval endpoints require ISO dates and explicit hours/minutes")
    if len(value) >= 6 and value[-6] in "+-" and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        raise ValueError("datetime offsets require hours 00-23 and minutes 00-59")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _availability(data: dict[str, Any]) -> dict[str, Any]:
    people = _require(data, "people")
    if not isinstance(people, list) or not all(isinstance(person, dict) for person in people):
        raise ValueError("people must be a nonempty array of participant objects")
    required = data.get("minimum_people", len(people))
    if not isinstance(required, int) or isinstance(required, bool):
        raise TypeError("minimum_people must be an integer")
    if required < 1 or required > len(people):
        raise ValueError("minimum_people is outside the participant count")
    minimum = data.get("minimum_minutes", 0)
    buffer = data.get("buffer_minutes", 0)
    for key, value in (("minimum_minutes", minimum), ("buffer_minutes", buffer)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{key} must be a nonnegative integer")
    mode = data.get("timezone_mode", "auto")
    if not isinstance(mode, str) or mode not in {"auto", "utc", "naive"}:
        raise ValueError("timezone_mode must be auto, utc, or naive")
    required_ids = data.get("required_participant_ids", [])
    if not isinstance(required_ids, list) or not all(
        isinstance(identity, str) and identity.strip() for identity in required_ids
    ):
        raise ValueError("required_participant_ids must be an array of nonempty participant IDs")
    required_set = set(required_ids)
    if len(required_set) != len(required_ids):
        raise ValueError("required_participant_ids must not contain duplicates")
    events = []
    names: dict[str, str] = {}
    aware_seen: bool | None = None
    for person in people:
        name = _require(person, "name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("participant names must be nonempty strings")
        identity = person.get("id", name)
        if not isinstance(identity, str) or not identity.strip() or identity in names:
            raise ValueError("participant IDs must be nonempty and unique (name is the default ID)")
        names[identity] = name
        intervals = person.get("intervals", [])
        if not isinstance(intervals, list):
            raise TypeError(f"intervals for {identity} must be an array")
        ranges: list[tuple[datetime, datetime]] = []
        for interval in intervals:
            if (
                not isinstance(interval, list)
                or len(interval) != 2
                or not all(isinstance(value, str) for value in interval)
            ):
                raise ValueError(f"intervals for {identity} must contain start/end string pairs")
            start, end = (_datetime(value) for value in interval)
            for moment in (start, end):
                aware = moment.utcoffset() is not None
                if (
                    aware_seen is not None
                    and aware != aware_seen
                    or mode == "utc"
                    and not aware
                    or mode == "naive"
                    and aware
                ):
                    raise ValueError("datetime forms must be consistently offset-aware or naive")
                aware_seen = aware
            if aware_seen:
                try:
                    start, end = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
                except OverflowError as exc:
                    raise ValueError(
                        "UTC datetimes must remain within years 1 through 9999"
                    ) from exc
            if end <= start:
                raise ValueError("availability intervals must end after they start")
            ranges.append((start, end))
        union: list[tuple[datetime, datetime]] = []
        for start, end in sorted(ranges):
            if union and start <= union[-1][1]:
                union[-1] = (union[-1][0], max(end, union[-1][1]))
            else:
                union.append((start, end))
        for start, end in union:
            if (end - start).total_seconds() <= buffer * 120:
                continue
            start, end = start + timedelta(minutes=buffer), end - timedelta(minutes=buffer)
            if end > start:
                events.extend([(start, 1, identity), (end, -1, identity)])
    if not required_set.issubset(names):
        raise ValueError("required_participant_ids contains an unknown participant ID")
    events.sort(key=lambda item: (item[0], item[1]))
    active: dict[str, int] = {}
    overlaps: list[dict[str, Any]] = []
    previous: datetime | None = None
    for moment, change, name in events:
        if (
            previous is not None
            and moment > previous
            and len(active) >= required
            and required_set.issubset(active)
        ):
            overlaps.append(
                {
                    "start": previous.isoformat(),
                    "end": moment.isoformat(),
                    "people": sorted(active),
                    "minutes": int((moment - previous).total_seconds() / 60),
                }
            )
        active[name] = active.get(name, 0) + change
        if active[name] == 0:
            del active[name]
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
    return {
        "overlaps": [item for item in merged if item["minutes"] >= minimum],
        **(
            {"required_participant_ids": required_ids} if "required_participant_ids" in data else {}
        ),
        "minimum_people": required,
        "participant_names": names,
        "minimum_minutes": minimum,
        "buffer_minutes": buffer,
        "timezone": "UTC" if aware_seen else "naive wall time (no timezone conversion)",
    }


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise TypeError("input must be a JSON object")
    return {"version": 1, "project": PROJECT, **_availability(data)}


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n"


def _markdown_text(value: str) -> str:
    escaped = html.escape(value, quote=False).replace("\r", " ").replace("\n", " ")
    return re.sub(r"([\\`*{}\[\]()#+.!_|~])", r"\\\1", escaped)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [f"# {report['project'].replace('-', ' ').title()} report", ""]
    lines.extend(
        [
            f"Timezone: {report['timezone']}",
            "",
            "| Start | End | Minutes | Participants |",
            "|---|---|---:|---|",
        ]
    )
    for slot in report["overlaps"]:
        people = ", ".join(_markdown_text(value) for value in slot["people"])
        lines.append(f"| {slot['start']} | {slot['end']} | {slot['minutes']} | {people} |")
    lines.append("")
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
