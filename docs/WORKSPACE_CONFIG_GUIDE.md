# Workspace Configuration Guide

This workspace uses several strategies to maintain DRY (Don't Repeat Yourself) principles:

## 1. Tool Configurations (in root pyproject.toml)

Tool configurations like `[tool.ruff]`, `[tool.pytest.ini_options]` are defined at the workspace root and inherited by all members.

## 2. Dependency Version Constraints

The root `pyproject.toml` defines `[tool.uv.constraint-dependencies]` to ensure version consistency across all workspace members.

## 3. Template Files

- `dependency-groups-template.toml` - Copy sections as needed into individual workspace members
- `pyproject-shared.toml` - Alternative shared configuration approach

## 4. Workspace Sources

The `[tool.uv.sources]` section ensures workspace members can reference each other consistently.

## 5. Custom Indexes

PyTorch CPU and CUDA indexes are defined once at the workspace level.

## Usage in Workspace Members

In individual workspace member `pyproject.toml` files:

```toml
[project]
name = "my-workspace-member"
# ... project-specific config

[dependency-groups]
# Copy from template and customize
dev = [
    "my-project-specific-dev-tool>=1.0.0",
    # Add common dev dependencies from template
]

# Inherit tool configurations automatically from workspace root
# Override only if needed:
[tool.ruff.lint]
# Add project-specific overrides if needed
extend-ignore = ["D101"]  # Allow missing docstrings in this specific project
```

## Benefits

1. **Consistency**: All projects use the same tool configurations and compatible dependency versions
2. **Maintainability**: Update tool configs once at the workspace root
3. **Flexibility**: Individual projects can still override or extend configurations as needed
4. **Dependency Management**: UV ensures compatible versions across the entire workspace

## Appendices

### Dependency Group Examples

```
# Common dependency groups template
# Use this as a reference for consistent dependency groups across workspace members
#
# To use in workspace members:
# 1. Copy the sections you need
# 2. Add project-specific dependencies as needed
# 3. Override versions if required for specific projects

[dependency-groups]
# Development dependencies - common across all projects
dev = [
  "autopep8>=2.3.2",
  "pytest>=8.3.4", 
  "pytest-asyncio>=0.26.0",
  "ruff>=0.9.2",
]

# Testing dependencies
test = [
  "pytest>=8.3.4",
  "pytest-asyncio>=0.26.0",
  "pytest-cov>=5.0.0",
  "pytest-mock>=3.12.0",
]

# Documentation dependencies
docs = [
  "mkdocs>=1.5.3",
  "mkdocs-material>=9.4.0",
  "mkdocstrings[python]>=0.24.0",
]

# ML/AI common dependencies
ml-common = [
  "numpy>=1.24.0",
  "pandas>=2.0.0",
  "scikit-learn>=1.3.0",
]

[project.optional-dependencies]
# PyTorch CPU variant
cpu = [
  "torch>=2.5.1",
  "torchaudio>=2.5.1", 
  "torchvision>=0.20.0"
]

# PyTorch CUDA variant
cuda13 = [
  "torch>=2.5.1",
  "torchaudio>=2.5.1",
  "torchvision>=0.20.0"
]

# Web/API dependencies
web = [
  "fastapi>=0.104.0",
  "uvicorn[standard]>=0.24.0",
  "pydantic>=2.5.0",
]

# Database dependencies
db = [
  "sqlalchemy>=2.0.0",
  "alembic>=1.13.0",
  "asyncpg>=0.29.0",  # PostgreSQL async driver
]

# Monitoring/observability
monitoring = [
  "prometheus-client>=0.19.0",
  "opentelemetry-api>=1.21.0",
  "opentelemetry-sdk>=1.21.0",
]

```

### Shared pyproject.toml

```
# Shared configurations for all workspace members
# This file can be imported by individual workspace members

[dependency-groups]
dev = [
  "autopep8>=2.3.2",
  "pytest>=8.3.4",
  "pytest-asyncio>=0.26.0",
  "ruff>=0.9.2",
]

[project.optional-dependencies]
cpu = [
  "torch>=2.5.1",
  "torchaudio>=2.5.1",
  "torchvision>=0.20.0"
]
cuda13 = [
  "torch>=2.5.1",
  "torchaudio>=2.5.1",
  "torchvision>=0.20.0"
]

[tool.ruff]
include = ["pyproject.toml", "src/**/*.py", "tests/**/*.py"]
line-length = 120

[tool.ruff.format]
quote-style = "single"
indent-style = "space"
docstring-code-format = true
skip-magic-trailing-comma = true

[tool.ruff.lint]
select = ["E", "F", "W", "C", "D"]
ignore = [
  "D100", # Suppress D100 Missing docstring in public module
  "D103", # Suppress D103 Missing docstring in public function
  "D104", # Suppress D104 Missing docstring in public package
  "D203", # Suppress D203 Use a blank line to separate the docstring from the class definition
  "D212", # Supress D212 Multi-line docstring summary should start at the first line
  "D401", # Suppres D401 First line of docstring should be in imperative mood
  "D404" # Suppress D404 First word of the docstring should not be "This"
]

[tool.ruff.lint.pycodestyle]
max-doc-length = 100

```