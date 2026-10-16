# Changelog

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

## 1.1.0 - 2026-09-07

- Union participant intervals, validate identities and datetime forms, and add meeting-length filters, buffers and a UTC-aware timeline.
- Added regression coverage for the audited behavior and invalid inputs.

## 1.0.0 - 2026-07-26

- Released the first complete Multi-Person Availability Merger command-line workflow.
- Added deterministic reporting, representative examples, cross-platform tests, and explicit limitations.
