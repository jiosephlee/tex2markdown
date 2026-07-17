# Contributing

Install the development environment with `uv sync`, then run `uv run pytest` and
`uv run ruff check .` before submitting a change.

Conversion changes must include a focused synthetic regression test. Changes that affect the
accepted strategy should also be checked against the private ClaimSpy fixed cohort; do not add
arXiv source files or generated corpus documents to this repository.
