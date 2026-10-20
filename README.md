# Multi-Person Availability Merger

[![CI](https://github.com/loganpendragonmultiverse/multi-person-availability-merger/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/multi-person-availability-merger/actions/workflows/ci.yml)

Merge pasted availability lists and return overlapping windows without calendar access. The command uses explicit UTF-8 JSON input and produces reviewable JSON or Markdown output.

## Three-minute start

```bash
python -m pip install .
availability-merge examples/sample.json
availability-merge examples/sample.json --format json --output report.json
```

The example documents the v1 input shape. Existing report files are never overwritten. Source inputs are read-only except where the documented purpose explicitly creates a new output artifact.

## Privacy and platforms

The tool runs locally and does not upload input or include telemetry. Python 3.10 or newer is supported on Windows, macOS, and Linux.

## Interpretation boundary

Intervals use explicit ISO datetimes. The tool does not resolve time zones, recurring events, travel time, or calendar conflicts not supplied.

## Development

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy src
pytest
python -m build
```

The project is feature-complete for its documented v1 scope. Maintenance focuses on correctness, security, compatibility, and well-supported input improvements.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).

## Version 1.1.0: reviewed improvements

Union participant intervals, validate identities and datetime forms, and add meeting-length filters, buffers and a UTC-aware timeline.

```bash
availability-merge examples/sample.json --format markdown
```

Each person may provide a unique string `id`; otherwise their unique name is the ID. Use `minimum_minutes` and `buffer_minutes` as nonnegative integers. Buffers trim each person's unioned availability before calculating overlaps; meeting length applies to each continuous slot with the same participant set. `timezone_mode` is `auto`, `utc` (explicit offsets required), or `naive` (wall times only). Offset-aware inputs are converted to UTC before duration arithmetic. Mixed aware/naive times and duplicate IDs are rejected. Named-zone guessing and calendar writes are not performed. Markdown includes a start/end/minutes/participants timeline.

## 1.2.0 - 2026-10-16

Optional `required_participant_ids` restricts results to windows containing every listed ID as
well as the `minimum_people` quorum. IDs must be unique, nonempty strings already present in
`people`; omitted IDs preserve the existing report shape and behavior. An explicit empty list
adds no constraint. Names remain display labels, so people with identical names need distinct IDs.

For example, use `"minimum_people": 2, "required_participant_ids": ["organizer"]` to require the
organizer plus at least one other participant. Buffers still trim each person's unioned intervals,
and the duration filter applies to each continuous window with the same participant set.
Explicit offsets retain UTC arithmetic across transitions. No calendar access, invitations,
time-zone guessing, or inferred availability is added.

## 1.2.1 completion pass

Participant names must be nonempty strings. Interval endpoints require an ISO date
and explicit hour/minute clock separated by `T` or a space, with optional seconds
(up to six fractional digits) and optional `Z` or `±HH:MM` offset. Date-only and
compact/ambiguous forms are rejected. Offset minutes must be 00–59; UTC conversion
must stay within years 1–9999. A buffer longer than a participant's window simply
removes that window, including very large buffer values.

Reports are created exclusively, so an existing destination or symlink cannot be
overwritten even if it appears between validation and writing. Markdown participant
IDs are rendered as literal text; JSON preserves supplied IDs. The intended scope
is complete: explicit intervals, unions, buffers, quorum and required participants,
UTC arithmetic and read-only-source report export. No calendar service is contacted.
