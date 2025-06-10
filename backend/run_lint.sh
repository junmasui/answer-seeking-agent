# Handle specific autopep8-only fixes first
#
# E402 - Import placement issues
# E501 - Line length violations (general code, not just docstrings)
# E502 - Extraneous escape of newline
# W503/W504 - Line break operator positioning
# W605 - Invalid escape sequences
#
# E261 - Fix spacing after inline comment hash.
# E262 - Fix spacing after inline comment hash.
# E265 - Fix spacing after block comment hash.
# E266 - Fix too many block comment hashes.
#
uvx autopep8 \
  --max-line-length=120 \
  --select=E402,E501,E502,W503,W504,W605 \
  --in-place --recursive src/core/agent/
  # src tests

# Fix doc line length (W505) - wrap docstrings at 100 characters to match ruff config
uvx docformatter \
  --wrap-summaries 100 --wrap-descriptions 100 \
  --in-place --recursive  src/core/agent/
  # src tests

# Sort the import statement
uvx ruff check --select I --fix src tests

# D202 No blank lines after doc-strings
# D213 Multi-line doc-string summary start on 2nd line
uvx ruff check --select D202,D213 --fix src tests/
# One line doc-strings should be on one line
uvx ruff check --select D200 --unsafe-fixes --fix src tests/

uvx ruff check --fix
uvx ruff format
