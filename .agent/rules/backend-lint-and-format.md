---
trigger: glob
globs: **/*.py, **/*.toml
---

# Backend Linting and Formatting

Use `uv run ruff check` / `uv run ruff format`.
DO NOT use black or isort directly as Ruff handles this.