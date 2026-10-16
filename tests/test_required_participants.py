import copy
import json

import pytest

from availability_merger.cli import main
from availability_merger.core import analyze


def fixture():
    return {
        "minimum_people": 2,
        "people": [
            {
                "id": "organizer",
                "name": "Alex",
                "intervals": [["2026-10-16T09:30Z", "2026-10-16T10:30Z"]],
            },
            {
                "id": "guest-a",
                "name": "Alex",
                "intervals": [["2026-10-16T09:00Z", "2026-10-16T11:00Z"]],
            },
            {
                "id": "guest-b",
                "name": "Guest",
                "intervals": [["2026-10-16T09:00Z", "2026-10-16T11:00Z"]],
            },
        ],
    }


def test_required_organizer_with_quorum():
    data = fixture()
    assert len(analyze(data)["overlaps"]) == 3
    data["required_participant_ids"] = ["organizer"]
    report = analyze(data)
    assert len(report["overlaps"]) == 1
    assert report["overlaps"][0]["people"] == ["guest-a", "guest-b", "organizer"]
    data["people"][0]["intervals"] = []
    assert analyze(data)["overlaps"] == []


@pytest.mark.parametrize(
    "ids", [["organizer", "organizer"], ["unknown"], [""], [1], "organizer", None]
)
def test_invalid_required_ids(ids):
    data = fixture()
    data["required_participant_ids"] = ids
    with pytest.raises(ValueError, match="required_participant_ids"):
        analyze(data)


def test_omission_and_explicit_empty_parity_without_mutation():
    data = fixture()
    original = copy.deepcopy(data)
    omitted = analyze(data)
    assert data == original
    assert "required_participant_ids" not in omitted
    data["required_participant_ids"] = []
    explicit = analyze(data)
    assert explicit.pop("required_participant_ids") == []
    assert explicit == omitted


def test_buffers_and_minimum_duration_apply_after_requirement():
    data = fixture()
    data.update(required_participant_ids=["organizer"], buffer_minutes=15, minimum_minutes=30)
    result = analyze(data)["overlaps"]
    assert len(result) == 1
    assert result[0]["minutes"] == 30
    assert result[0]["start"] == "2026-10-16T09:45:00+00:00"
    data["minimum_minutes"] = 31
    assert analyze(data)["overlaps"] == []


@pytest.mark.parametrize(
    "start,end",
    [
        ("2026-03-08T01:30-05:00", "2026-03-08T03:30-04:00"),
        ("2026-11-01T01:30-04:00", "2026-11-01T01:30-05:00"),
    ],
)
def test_required_ids_with_explicit_offset_transitions(start, end):
    data = {
        "minimum_people": 1,
        "required_participant_ids": ["host"],
        "people": [{"id": "host", "name": "Host", "intervals": [[start, end]]}],
        "minimum_minutes": 60,
    }
    assert analyze(data)["overlaps"][0]["minutes"] == 60


def test_cli_unknown_id_is_clean_error(tmp_path, capsys):
    data = fixture()
    data["required_participant_ids"] = ["missing"]
    source = tmp_path / "synthetic.json"
    source.write_text(json.dumps(data))
    assert main([str(source)]) == 2
    assert "unknown participant ID" in capsys.readouterr().err
