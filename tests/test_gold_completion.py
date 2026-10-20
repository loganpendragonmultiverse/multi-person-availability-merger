import json
from pathlib import Path

import pytest

from availability_merger.cli import main
from availability_merger.core import analyze, render_markdown


def data(start="2026-10-20T09:00", end="2026-10-20T10:00"):
    return {"people": [{"name": "Host", "intervals": [[start, end]]}]}


@pytest.mark.parametrize("name", [1, True, {}, [], " ", "\t"])
def test_names_require_nonempty_text(name):
    source = data()
    source["people"][0]["name"] = name
    with pytest.raises(ValueError):
        analyze(source)


@pytest.mark.parametrize(
    "start",
    [
        "2026-10-20",
        "20261020T090000",
        "2026-10-20x09:00",
        "2026-10-20T09:00+00:60",
        "2026-10-20T09:00+24:00",
    ],
)
def test_datetime_requires_explicit_clock_and_valid_offset(start):
    with pytest.raises(ValueError):
        analyze(data(start))


def test_huge_buffer_means_no_windows_without_timedelta_overflow():
    source = data()
    source["buffer_minutes"] = 10**100
    assert analyze(source)["overlaps"] == []


def test_utc_boundary_failure_is_clean_cli_error(tmp_path, capsys):
    source = tmp_path / "source.json"
    source.write_text(json.dumps(data("0001-01-01T00:00+01:00", "0001-01-01T02:00+01:00")))
    assert main([str(source)]) == 2
    assert "UTC datetimes" in capsys.readouterr().err


def test_markdown_participant_ids_are_literal_text():
    source = data()
    source["people"][0]["id"] = "<img src=x onerror=alert(1)>|[x](https://example.org)\r\n*host*"
    report = analyze(source)
    text = render_markdown(report)
    table = text.split("## Overlaps")[0]
    assert "<img" not in table
    assert "&lt;img" in table
    assert "\\|" in table
    assert "\\[x\\]" in table
    assert "\r" not in table
    assert report["overlaps"][0]["people"] == [source["people"][0]["id"]]


def test_output_creation_is_exclusive_without_precheck(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    source.write_text(json.dumps(data()))
    output = tmp_path / "report.json"
    original_open = Path.open

    def racing_open(path, mode="r", *args, **kwargs):
        if path == output and mode == "x":
            with original_open(output, "w") as writer:
                writer.write("another process")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", racing_open)
    assert main([str(source), "--format", "json", "--output", str(output)]) == 2
    assert output.read_text() == "another process"


def test_source_path_and_dangling_symlink_are_not_overwritten(tmp_path):
    source = tmp_path / "source.json"
    raw = json.dumps(data())
    source.write_text(raw)
    assert main([str(source), "--output", str(source)]) == 2
    assert source.read_text() == raw
    link = tmp_path / "report.json"
    target = tmp_path / "not-created.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable")
    assert main([str(source), "--output", str(link)]) == 2
    assert not target.exists()


def test_markdown_quotes_remain_literal_without_corrupted_entities():
    source = data()
    source["people"][0]["id"] = 'O\'Reilly "Host"'
    table = render_markdown(analyze(source)).split("## Overlaps")[0]
    assert 'O\'Reilly "Host"' in table
    assert "&#" not in table
