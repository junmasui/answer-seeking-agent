# Example: Complete DRY Workspace Configuration

## Root pyproject.toml (What we have now)

- Tool configurations (`[tool.ruff]`, `[tool.pytest.ini_options]`) - inherited by all members
- Dependency version constraints (`[tool.uv.constraint-dependencies]`) - ensures compatibility
- Workspace member definitions (`[tool.uv.workspace]`)
- Shared source mappings (`[tool.uv.sources]`)
- Global PyTorch indexes for CPU/CUDA variants

## Individual Workspace Member Pattern

Each workspace member can now:

1. **Reference common tools** - automatically inherit Ruff, pytest configs from root
2. **Use constrained versions** - UV ensures compatible versions via constraint-dependencies
3. **Define project-specific dependencies** - while following workspace patterns
4. **Extend rather than duplicate** - add project-specific needs to common base

## Example Member Structure

```toml
[project]
name = "my-app"
dependencies = [
    # Workspace dependencies
    "core",
    "core-db", 
    # External dependencies (versions constrained at workspace level)
    "fastapi[standard]",
    "sqlalchemy",
]

[dependency-groups]
# Common dev tools (versions managed at workspace level)
dev = [
    "pytest",      # Version constrained in workspace
    "ruff",        # Version constrained in workspace
    "autopep8",    # Version constrained in workspace
    # Project-specific additions
    "httpx>=0.25.0",
]

# Project-specific groups
api-testing = [
    "httpx",
    "respx>=0.20.0",
]

[project.optional-dependencies]
# Inherit workspace CPU/CUDA definitions
cpu = []     # References workspace torch[cpu] configuration
cuda12 = []  # References workspace torch[cuda12] configuration

# Add project-specific optionals
monitoring = [
    "prometheus-client",  # Version constrained at workspace level
]
```

## Benefits of This Approach

1. **Single Source of Truth**: Tool configurations and version constraints defined once
2. **Consistency**: All projects use compatible versions and same tools
3. **Flexibility**: Projects can add specific dependencies while following common patterns
4. **Maintainability**: Update tool configs or constraints in one place
5. **UV Integration**: Leverages UV's workspace features for dependency resolution
