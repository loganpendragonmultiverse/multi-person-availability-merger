# Development contract

Merge pasted availability lists and return overlapping windows without calendar access.

Preserve deterministic, source-safe behavior and the interpretation boundary documented in the README. Every feature release must update tests, version metadata, changelog, README claims, repository metadata, release assets, and the Forge catalog together.

## 1.1.0 improvement session

Union participant intervals, validate identities and datetime forms, and add meeting-length filters, buffers and a UTC-aware timeline.

Each person may provide a unique string `id`; otherwise their unique name is the ID. Use `minimum_minutes` and `buffer_minutes` as nonnegative integers. Buffers trim each person's unioned availability before calculating overlaps; meeting length applies to each continuous slot with the same participant set. `timezone_mode` is `auto`, `utc` (explicit offsets required), or `naive` (wall times only). Offset-aware inputs are converted to UTC before duration arithmetic. Mixed aware/naive times and duplicate IDs are rejected. Named-zone guessing and calendar writes are not performed. Markdown includes a start/end/minutes/participants timeline.

Local formatting, lint, strict types and regression tests pass. Public release completion requires the protected CI/CodeQL matrix, tagged artifacts and matching Forge catalog/detail deployment.
