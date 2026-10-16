# Testing

Run `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, and `python -m build`. CI also audits dependencies and runs the supported OS/Python matrix.

Required-participant regression fixtures cover an absent organizer with a satisfied quorum,
duplicate/unknown/malformed IDs, omission parity, empty IDs, buffers and duration boundaries,
same-name participants with distinct IDs, explicit-offset transitions, and CLI validation.
All fixtures are synthetic and require no calendar services.
