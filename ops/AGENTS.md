# Ops / Dagster Agent Operating Guide

## Package Management (uv)

- **Tooling**: Strictly use `uv` for all Python operations.
- **Commands**:
  - `uv add <pkg>`: Add dependencies.
  - `uv run <script>`: Run scripts.
  - `uv run pytest`: Run tests.
  - `uv run ruff check`: Lint workspace.
  - `uv run ruff format`: Format workspace.

## Dagster specific workflows

- **Home Dir**: `DAGSTER_HOME` env var must be set (see `ops/README.md`).
- **Workspace**: `workspace.yaml` loads definitions from `/defs/`.
- **Assets**: Use asset observations and sensors for state.

## Code Style & Conventions

- **Formatting**: Rely on `ruff` (120 chars, single quotes). No `black`/`isort`.
- **Imports**: Group into Stdlib, Third-party (Dagster, Pydantic, etc.), Local.
- **Naming**: `snake_case` for assets/jobs/ops.

## Golden Path Implementation

### Dagster Asset

```python
from dagster import asset, Output, AssetExecutionContext

@asset(
    group_name="core_pipeline",
    compute_kind="python"
)
def clean_documents(context: AssetExecutionContext, raw_docs: list[dict]) -> Output[list[dict]]:
    """Clean raw documents and standardise schema."""
    context.log.info(f"Processing {len(raw_docs)} documents")
    
    cleaned = [d for d in raw_docs if d.get('text')]
    
    # Return Output with metadata
    return Output(
        value=cleaned,
        metadata={"count": len(cleaned), "ratio": len(cleaned)/len(raw_docs)}
    )
```

## Testing

- **Tests Location**: `ops/tests/test_assets/`.
- **Unit Testing**:

  ```python
  from dagster import build_op_context
  from ops.assets.documents import clean_documents

  def test_clean_documents():
      context = build_op_context()
      result = clean_documents(context, raw_docs=[{'text': 'foo'}, {}])
      assert len(result.value) == 1
  ```

- **Run**: `uv run pytest ops/tests`
