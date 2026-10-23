# Testing

Run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`. CI runs the supported OS/Python matrix. The runtime has no third-party dependencies.

Required-participant regression fixtures cover an absent organizer with a satisfied quorum,
duplicate/unknown/malformed IDs, omission parity, empty IDs, buffers and duration boundaries,
same-name participants with distinct IDs, explicit-offset transitions, and CLI validation.
All fixtures are synthetic and require no calendar services.

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

## Native CI architecture mapping

The complete existing six-cell matrix and test commands remain required. The
`macos-latest, 3.10` check runs on the standard `macos-26-intel` image (macOS 26,
Intel); the `macos-latest, 3.14` check retains the standard current macOS ARM
image. Linux and Windows still test both Python 3.10 and 3.14. The explicit
older-Python mapping avoids the observed ARM runner allocation failures while
retaining native macOS coverage, every check name and the coverage threshold.
It does not change branch protection, workflow permissions or test selection.

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
