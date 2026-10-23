import copy
import io
import json
import subprocess
import sys
from datetime import datetime, timezone

import pytest
from icalendar import Calendar

from availability_merger.calendar_export import render_ics
from availability_merger.cli import main
from availability_merger.core import analyze


def sample():
    return {
        "people": [
            {
                "id": "private-a",
                "name": "Alex",
                "intervals": [
                    ["2026-10-25T01:00:00", "2026-10-25T02:00:00"],
                    ["2026-10-25T04:00:00", "2026-10-25T05:00:00"],
                ],
            },
            {
                "id": "private-b",
                "name": "Blair",
                "intervals": [["2026-10-25T00:00:00", "2026-10-25T06:00:00"]],
            },
        ]
    }


def events(text):
    return Calendar.from_ical(text.encode("utf-8")).walk("VEVENT")


def test_only_selected_overlap_and_explicit_offset_preserve_input():
    report = analyze(sample())
    before = copy.deepcopy(report)
    text = render_ics(report, [2], timezone_choice="+05:30", privacy="busy-only")
    parsed = events(text)
    assert len(parsed) == 1
    event = parsed[0]
    assert event.decoded("dtstart") == datetime(2026, 10, 24, 22, 30, tzinfo=timezone.utc)
    assert event.decoded("dtend") == datetime(2026, 10, 24, 23, 30, tzinfo=timezone.utc)
    assert str(event["SUMMARY"]) == "Selected overlap"
    assert str(event["STATUS"]) == "TENTATIVE"
    assert str(event["CLASS"]) == "PRIVATE"
    assert str(event["TRANSP"]) == "OPAQUE"
    assert event.decoded("dtstamp").utcoffset().total_seconds() == 0
    assert "DESCRIPTION" not in event
    assert set(event) == {
        "UID",
        "DTSTAMP",
        "DTSTART",
        "DTEND",
        "SUMMARY",
        "STATUS",
        "CLASS",
        "TRANSP",
    }
    assert all(value not in text for value in ["private-a", "private-b", "Alex", "Blair"])
    assert report == before
    assert text.endswith("\r\n") and "\n" not in text.replace("\r\n", "")


def test_aware_instants_keep_utc_arithmetic_across_offset_transition():
    data = {
        "people": [
            {
                "name": "Person",
                "intervals": [["2026-10-25T01:30:00+02:00", "2026-10-25T02:30:00+01:00"]],
            }
        ]
    }
    report = analyze(data)
    event = events(render_ics(report, [1], timezone_choice="UTC", privacy="busy-only"))[0]
    assert event.decoded("dtstart") == datetime(2026, 10, 24, 23, 30, tzinfo=timezone.utc)
    assert (event.decoded("dtend") - event.decoded("dtstart")).total_seconds() == 7200
    with pytest.raises(ValueError, match="already define instants"):
        render_ics(report, [1], timezone_choice="+01:00", privacy="busy-only")


@pytest.mark.parametrize(
    "zone,hour,day", [("UTC", 1, 25), ("-05:00", 6, 25), ("+14:00", 11, 24), ("-14:00", 15, 25)]
)
def test_explicit_naive_timezone_choices(zone, hour, day):
    report = analyze(sample())
    event = events(render_ics(report, [1], timezone_choice=zone, privacy="busy-only"))[0]
    assert event.decoded("dtstart") == datetime(2026, 10, day, hour, tzinfo=timezone.utc)


def test_participant_opt_in_escapes_and_folds_utf8_without_injecting_properties():
    data = sample()
    name = "Zoë😀;" * 30 + ",\\\r\nATTENDEE:mailto:example@example.invalid"
    data["people"][0]["name"] = name
    data["people"][1]["name"] = data["people"][1]["id"]
    report = analyze(data)
    text = render_ics(report, [2, 1], timezone_choice="UTC", privacy="participants")
    for line in text.split("\r\n"):
        assert len(line.encode("utf-8")) <= 75
    assert "\r\n " in text
    calendar = Calendar.from_ical(text.encode("utf-8"))
    parsed = calendar.walk("VEVENT")
    assert len(parsed) == 2 and parsed[0].decoded("dtstart").hour == 4
    assert str(parsed[0]["description"]) == (
        "Participants: " + name.replace("\r\n", "\n") + " (private-a), private-b"
    )
    assert len({str(event["UID"]) for event in parsed}) == 2
    assert not any(key in event for event in parsed for key in ("ATTENDEE", "ORGANIZER", "URL"))
    assert "METHOD" not in calendar
    assert len(calendar.walk("VALARM")) == 0


def test_each_export_gets_fresh_nonpersonal_uid():
    report = analyze(sample())
    first = events(render_ics(report, [1], timezone_choice="UTC", privacy="busy-only"))[0]
    second = events(render_ics(report, [1], timezone_choice="UTC", privacy="busy-only"))[0]
    assert first["UID"] != second["UID"]


@pytest.mark.parametrize("indices", [[], [0], [-1], [True], ["1"], [1, 1], [3], None])
def test_invalid_or_duplicate_selections_are_rejected(indices):
    with pytest.raises(ValueError):
        render_ics(analyze(sample()), indices, timezone_choice="UTC", privacy="busy-only")


@pytest.mark.parametrize(
    "zone", ["", "local", "Europe/London", "+14:01", "-14:30", "+25:00", "+01:60", "-00:00", None]
)
def test_no_timezone_guessing_or_unknown_offsets(zone):
    with pytest.raises((TypeError, ValueError), match="calendar"):
        render_ics(analyze(sample()), [1], timezone_choice=zone, privacy="busy-only")


def test_invalid_privacy_report_precision_and_control_characters():
    report = analyze(sample())
    with pytest.raises(ValueError, match="privacy"):
        render_ics(report, [1], timezone_choice="UTC", privacy="all")
    with pytest.raises(TypeError, match="analyzed"):
        render_ics({}, [1], timezone_choice="UTC", privacy="busy-only")
    report["overlaps"][0]["start"] = "2026-10-25T01:00:00.500000"
    with pytest.raises(ValueError, match="whole-second"):
        render_ics(report, [1], timezone_choice="UTC", privacy="busy-only")
    report["overlaps"][0]["start"] = None
    with pytest.raises(TypeError, match="datetime strings"):
        render_ics(report, [1], timezone_choice="UTC", privacy="busy-only")
    report = analyze(sample())
    report["participant_names"]["private-a"] = "Alex\x00"
    with pytest.raises(ValueError, match="control"):
        render_ics(report, [1], timezone_choice="UTC", privacy="participants")
    assert events(render_ics(report, [1], timezone_choice="UTC", privacy="busy-only"))
    report["overlaps"][0]["end"] = report["overlaps"][0]["start"]
    with pytest.raises(ValueError, match="end after"):
        render_ics(report, [1], timezone_choice="UTC", privacy="busy-only")


def test_year_padding_overflow_and_seconds():
    report = analyze(sample())
    slot = report["overlaps"][0]
    slot.update(start="0001-01-01T01:00:01", end="0001-01-01T02:00:02")
    text = render_ics(report, [1], timezone_choice="UTC", privacy="busy-only")
    assert "DTSTART:00010101T010001Z" in text and "DTEND:00010101T020002Z" in text
    slot.update(start="0001-01-01T00:00:00", end="0001-01-01T00:01:00")
    with pytest.raises(ValueError, match="years"):
        render_ics(report, [1], timezone_choice="+01:00", privacy="busy-only")


def test_cli_file_crlf_and_no_overwrite(tmp_path, capsys):
    source = tmp_path / "availability.json"
    source.write_text(json.dumps(sample()), encoding="utf-8")
    before = source.read_bytes()
    output = tmp_path / "selected.ics"
    args = [
        str(source),
        "--format",
        "ics",
        "--slot",
        "1",
        "--calendar-timezone=-05:00",
        "--calendar-privacy",
        "busy-only",
        "--output",
        str(output),
    ]
    assert main(args) == 0
    raw = output.read_bytes()
    assert b"\r\n" in raw and b"\r\r\n" not in raw
    assert len(events(raw.decode())) == 1
    assert main(args) == 2
    assert output.read_bytes() == raw and source.read_bytes() == before
    assert "already exists" in capsys.readouterr().err


def test_cli_stdout_and_explicit_options(tmp_path, monkeypatch):
    source = tmp_path / "availability.json"
    source.write_text(json.dumps(sample()))
    text_stream = io.StringIO()
    monkeypatch.setattr("sys.stdout", text_stream)
    options = [
        str(source),
        "--format",
        "ics",
        "--slot",
        "1",
        "--calendar-timezone",
        "UTC",
        "--calendar-privacy",
        "participants",
    ]
    assert main(options) == 0
    assert len(events(text_stream.getvalue())) == 1
    for args in [
        [str(source), "--format", "ics"],
        [str(source), "--format", "ics", "--calendar-timezone", "UTC"],
        [str(source), "--format", "json", "--slot", "1"],
        [str(source), "--calendar-timezone", "UTC"],
        [str(source), "--calendar-privacy", "busy-only"],
    ]:
        assert main(args) == 2


def test_native_subprocess_stdout_is_utf8_crlf(tmp_path):
    data = sample()
    data["people"][0]["name"] = "Zoë 😀"
    source = tmp_path / "input.json"
    source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    before = source.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "availability_merger",
            str(source),
            "--format",
            "ics",
            "--slot",
            "1",
            "--calendar-timezone",
            "UTC",
            "--calendar-privacy",
            "participants",
        ],
        capture_output=True,
        check=True,
    )
    raw = result.stdout
    assert b"\r\n" in raw and b"\r\r\n" not in raw
    assert b"\n" not in raw.replace(b"\r\n", b"")
    assert b"Zo\xc3\xab" in raw and result.stderr == b""
    event = Calendar.from_ical(raw).walk("VEVENT")[0]
    assert "Zoë 😀 (private-a)" in str(event["DESCRIPTION"])
    assert source.read_bytes() == before
