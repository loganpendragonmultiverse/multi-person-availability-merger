# Development contract

Merge pasted availability lists and return overlapping windows without calendar access.

Preserve deterministic, source-safe behavior and the interpretation boundary documented in the README. Every feature release must update tests, version metadata, changelog, README claims, repository metadata, release assets, and the Forge catalog together.

## 1.1.0 improvement session

Union participant intervals, validate identities and datetime forms, and add meeting-length filters, buffers and a UTC-aware timeline.

Each person may provide a unique string `id`; otherwise their unique name is the ID. Use `minimum_minutes` and `buffer_minutes` as nonnegative integers. Buffers trim each person's unioned availability before calculating overlaps; meeting length applies to each continuous slot with the same participant set. `timezone_mode` is `auto`, `utc` (explicit offsets required), or `naive` (wall times only). Offset-aware inputs are converted to UTC before duration arithmetic. Mixed aware/naive times and duplicate IDs are rejected. Named-zone guessing and writes to calendar accounts are not performed. Markdown includes a start/end/minutes/participants timeline.

Local formatting, lint, strict types and regression tests pass. Public release completion requires the protected CI/CodeQL matrix, tagged artifacts and matching Forge catalog/detail deployment.

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

## 1.2.1 audited completion

Preserve the explicit-interval interpretation boundary and the existing output
schema. Regression coverage includes non-text/blank participant names, date-only
and ambiguous endpoint forms, offset-minute validation, UTC year overflow, huge
buffers, literal Markdown IDs and exclusive report creation under a simulated race
and dangling symlink. Run the full unchanged format/lint/type/coverage/build gates,
then install both release distributions and exercise the CLI examples and errors.

Installed wheels include the four authority documents and the synthetic sample at
`share/doc/multi-person-availability-merger` under Python's data prefix. Locate it
with `python -c "import sysconfig; print(sysconfig.get_path('data'))"`, then run
`availability-merge <prefix>/share/doc/multi-person-availability-merger/examples/sample.json`.
Release acceptance installs both the exact tag wheel and sdist into fresh environments,
checks those files and runs the CLI examples outside the source checkout.

## Selected-overlap calendar export (1.3.0)

First inspect a JSON or Markdown report, then explicitly choose one-based entries from its `overlaps` list. Export only the selected windows:

```bash
availability-merge input.json --format json
availability-merge input.json --format ics --slot 1 --slot 3 --calendar-timezone UTC --calendar-privacy busy-only --output selected.ics
availability-merge input.json --format ics --slot 1 --calendar-timezone=-05:00 --calendar-privacy participants --output selected-with-names.ics
```

ICS export requires at least one unique `--slot`, an explicit `--calendar-timezone` and an explicit `--calendar-privacy`. Slot numbers refer to this report's ordered overlap entries; changing inputs, filters, buffers or quorum can change the numbering. Each event uses the complete selected window, not an inferred meeting length.

For offset-aware inputs choose `UTC`: their existing instants are preserved. For naive wall times explicitly choose `UTC` or a known fixed `+/-HH:MM` offset within -14:00 through +14:00. Use the equals form for a negative offset as shown above. Named zones, daylight-saving inference and unknown `-00:00` offsets are not supported; supply explicit-offset source intervals for DST-sensitive dates. All exported event endpoints use UTC. Fractional seconds are rejected rather than rounded.

`busy-only` uses a generic title and omits participant names and IDs. `participants` includes the selected window's names and distinct IDs in its description. Both disclose the selected times. CLASS:PRIVATE is a calendar hint, not encryption or access control; review the file and your calendar's sharing settings before importing or sharing it.

Events are tentative opaque time blocks. The file sends no invitations, includes no attendee/organizer/alarm fields and accesses no calendar accounts. Each export creates fresh event IDs; importing the same windows repeatedly can create duplicates. The UTF-8 iCalendar file uses CRLF and folded content lines following [RFC 5545](https://www.rfc-editor.org/rfc/rfc5545.html).

JSON/Markdown defaults, overlap calculation, filters, source-read-only behavior and exclusive output creation remain unchanged. Calendar-only options with a non-ICS format are rejected. Installed-file and stdout checks cover line endings on the native platform matrix; parser acceptance does not claim testing in every calendar application. The independent `icalendar` parser is a development/test dependency only; runtime dependencies remain empty.
