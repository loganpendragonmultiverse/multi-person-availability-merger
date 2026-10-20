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
