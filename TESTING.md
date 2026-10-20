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
