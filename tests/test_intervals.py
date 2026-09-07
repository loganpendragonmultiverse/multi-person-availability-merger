import pytest

from availability_merger.core import analyze, render_markdown


def test_overlapping_intervals_union_before_buffer() -> None:
    data = {
        "people": [
            {
                "name": "A",
                "intervals": [
                    ["2026-09-07T09:00", "2026-09-07T11:00"],
                    ["2026-09-07T10:00", "2026-09-07T12:00"],
                ],
            },
            {"name": "B", "intervals": [["2026-09-07T09:00", "2026-09-07T12:00"]]},
        ],
        "buffer_minutes": 15,
        "minimum_minutes": 120,
    }
    report = analyze(data)
    assert len(report["overlaps"]) == 1
    assert report["overlaps"][0]["minutes"] == 150
    assert "09:15" in render_markdown(report)


@pytest.mark.parametrize(
    "start,end,minutes",
    [
        ("2026-03-08T01:30-05:00", "2026-03-08T03:30-04:00", 60),
        ("2026-11-01T01:30-04:00", "2026-11-01T01:30-05:00", 60),
    ],
)
def test_dst_uses_explicit_offsets(start: str, end: str, minutes: int) -> None:
    report = analyze(
        {"timezone_mode": "utc", "people": [{"name": "A", "intervals": [[start, end]]}]}
    )
    assert report["overlaps"][0]["minutes"] == minutes
    assert report["timezone"] == "UTC"


def test_same_names_distinct_ids_and_short_windows() -> None:
    people = [
        {"id": str(i), "name": "Alex", "intervals": [["2026-09-07T09:00Z", "2026-09-07T10:00Z"]]}
        for i in range(2)
    ]
    assert analyze({"people": people})["overlaps"][0]["people"] == ["0", "1"]
    assert analyze({"people": people, "minimum_minutes": 61})["overlaps"] == []
    assert analyze({"people": people, "buffer_minutes": 31})["overlaps"] == []


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        {"people": "A"},
        {"people": [None]},
        {"people": [{"name": "A"}], "minimum_people": True},
        {"people": [{"name": "A"}], "minimum_minutes": -1},
        {"people": [{"name": "A"}], "timezone_mode": "guess"},
        {"people": [{"name": "A"}, {"name": "A"}]},
        {"people": [{"name": "A", "intervals": "bad"}]},
        {"people": [{"name": "A", "intervals": [["bad"]]}]},
        {"people": [{"name": "A", "intervals": [["2026-09-07T09:00", "2026-09-07T10:00Z"]]}]},
    ],
)
def test_invalid_shapes_are_clean_errors(data: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        analyze(data)  # type: ignore[arg-type]
