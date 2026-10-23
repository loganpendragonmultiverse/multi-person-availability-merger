"""Explicit, local iCalendar export of selected overlap windows."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from .core import _datetime


def _chosen_timezone(value: str) -> timezone:
    if value == "UTC":
        return timezone.utc
    if not isinstance(value, str):
        raise TypeError("calendar timezone must be UTC or a fixed +/-HH:MM offset")
    match = re.fullmatch(r"([+-])(\d{2}):(\d{2})", value)
    if not match:
        raise ValueError("calendar timezone must be UTC or a fixed +/-HH:MM offset")
    hours, minutes = int(match[2]), int(match[3])
    if minutes > 59 or hours > 14 or (hours == 14 and minutes) or value == "-00:00":
        raise ValueError("calendar offset must be known and within -14:00 through +14:00")
    delta = timedelta(hours=hours, minutes=minutes)
    return timezone(delta if match[1] == "+" else -delta)


def _text(value: str) -> str:
    if any(ord(char) < 32 and char not in "\r\n\t" or ord(char) == 127 for char in value):
        raise ValueError("calendar participant details contain unsupported control characters")
    return (
        value.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _fold(value: str) -> str:
    lines: list[str] = []
    current = ""
    length = 0
    for char in value:
        size = len(char.encode("utf-8"))
        if length + size > 75:
            lines.append(current)
            current, length = " ", 1
        current += char
        length += size
    lines.append(current)
    return "\r\n".join(lines)


def _stamp(value: datetime) -> str:
    return (
        f"{value.year:04d}{value.month:02d}{value.day:02d}T"
        f"{value.hour:02d}{value.minute:02d}{value.second:02d}Z"
    )


def _endpoint(value: object, chosen: timezone) -> datetime:
    if not isinstance(value, str):
        raise TypeError("selected overlap endpoints must be datetime strings")
    moment = _datetime(value)
    if moment.microsecond:
        raise ValueError(
            "calendar export requires whole-second endpoints; no rounding is performed"
        )
    if moment.utcoffset() is None:
        moment = moment.replace(tzinfo=chosen)
    elif chosen != timezone.utc:
        raise ValueError("offset-aware overlaps already define instants; choose UTC for export")
    try:
        return moment.astimezone(timezone.utc)
    except OverflowError as exc:
        raise ValueError("calendar UTC endpoints must remain within years 1 through 9999") from exc


def render_ics(
    report: dict[str, Any],
    slot_indices: list[int],
    *,
    timezone_choice: str,
    privacy: str,
) -> str:
    """Export one-based selected slots, with explicit timezone and privacy choices."""
    chosen = _chosen_timezone(timezone_choice)
    if privacy not in ("busy-only", "participants"):
        raise ValueError("calendar privacy must be busy-only or participants")
    overlaps = report.get("overlaps")
    if not isinstance(overlaps, list):
        raise TypeError("calendar export requires an analyzed overlap report")
    if (
        not isinstance(slot_indices, list)
        or not slot_indices
        or any(isinstance(i, bool) or not isinstance(i, int) or i < 1 for i in slot_indices)
    ):
        raise ValueError("select at least one positive, one-based overlap number")
    if len(set(slot_indices)) != len(slot_indices):
        raise ValueError("selected overlap numbers must be unique")
    if any(i > len(overlaps) for i in slot_indices):
        raise ValueError("selected overlap number is outside this report")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Logan Pendragon Forge//Availability Merger//EN",
    ]
    created = _stamp(datetime.now(timezone.utc))
    for index in slot_indices:
        slot = overlaps[index - 1]
        start, end = _endpoint(slot["start"], chosen), _endpoint(slot["end"], chosen)
        if end <= start:
            raise ValueError("selected overlap must end after it starts")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uuid4()}@availability-merger.local",
                f"DTSTAMP:{created}",
                f"DTSTART:{_stamp(start)}",
                f"DTEND:{_stamp(end)}",
                "SUMMARY:Selected overlap",
                "STATUS:TENTATIVE",
                "CLASS:PRIVATE",
                "TRANSP:OPAQUE",
            ]
        )
        if privacy == "participants":
            names = report["participant_names"]
            labels = [
                names[identity]
                if names[identity] == identity
                else f"{names[identity]} ({identity})"
                for identity in slot["people"]
            ]
            lines.append("DESCRIPTION:" + _text("Participants: " + ", ".join(labels)))
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
