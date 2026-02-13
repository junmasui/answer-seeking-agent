# Backend Agent Operating Guide

## Package Management (uv)

- **Tooling**: Strictly use `uv` for all Python operations.
- **Commands**:
  - `uv add <pkg>`: Add dependencies.
  - `uv run <script>`: Run scripts.
  - `uv run pytest`: Run tests.
  - `uv run ruff check`: Lint workspace.
  - `uv run ruff format`: Format workspace.
- **Syncing**: If you change dependencies, sync with `uv sync --all-packages` (watch extras) and commit lockfiles.

## Project Structure

- **Apps vs Libs**:

  ```text
  backend/
  ├── apps/
  │   └── core_server/       # Explicit service executable
  │       ├── routers/       # API endpoints
  │       └── main.py        # Entrypoint
  └── libs/
      └── core_utils/        # Shared logic (logging, error handling)
  ```

- **Tests**: Tests live under `apps/.../tests` or `libs/.../tests`, following `test_*.py`.

## Golden Path Implementation

### FastAPI Router + Pydantic Model

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated

# Define Model with Config
class UserResponse(BaseModel):
    id: str
    username: str = Field(..., description="Unique username")
    
    model_config = {"from_attributes": True}

router = APIRouter()

# Use Annotated for Deps
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str) -> UserResponse:
    """Retrieve a user by ID."""
    # Logic here...
    if not found:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(id=user_id, username="alice")
```

## Code Style & Conventions

- **Formatting**: Strictly rely on `ruff`. Do not mention `black` or `isort`.
- **Imports**: Group into Stdlib, Third-party, Local. No wildcard imports.
- **Typing**:
  - Annotate public parameters.
  - Use `typing.Annotated` + `Query/Body` for FastAPI.
  - Prefer Pydantic `BaseModel` for contracts.
- **Naming**: `snake_case` for functions/vars, `PascalCase` for classes. Prefix routers with HTTP noun.

## Testing

- **Running Tests**:
  - Full suite: `uv run pytest`
  - Single test: `uv run pytest path/to/test.py::TestClass::test_method`
  - Pattern match: `uv run pytest -k <expression>`
- **Docker Workflow**: `docker compose --profile backend up -d` allows running tests inside the container via `docker compose exec api-server uv run pytest ...`.
