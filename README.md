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
