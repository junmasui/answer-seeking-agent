
# Sort the import statement
uvx ruff check --select I --fix src tests

# D202 No blank lines after doc-strings
# D213 Multi-line doc-string summary start on 2nd line
uvx ruff check --select D202,D213 --fix src tests/
# One line doc-strings should be on one line
uvx ruff check --select D200 --unsafe-fixes --fix src tests/

uvx ruff format
