# Development contract

Merge pasted availability lists and return overlapping windows without calendar access.

Preserve deterministic, source-safe behavior and the interpretation boundary documented in the README. Every feature release must update tests, version metadata, changelog, README claims, repository metadata, release assets, and the Forge catalog together.

## 1.1.0 improvement session

Union participant intervals, validate identities and datetime forms, and add meeting-length filters, buffers and a UTC-aware timeline.

Each person may provide a unique string `id`; otherwise their unique name is the ID. Use `minimum_minutes` and `buffer_minutes` as nonnegative integers. Buffers trim each person's unioned availability before calculating overlaps; meeting length applies to each continuous slot with the same participant set. `timezone_mode` is `auto`, `utc` (explicit offsets required), or `naive` (wall times only). Offset-aware inputs are converted to UTC before duration arithmetic. Mixed aware/naive times and duplicate IDs are rejected. Named-zone guessing and calendar writes are not performed. Markdown includes a start/end/minutes/participants timeline.

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
