# The conftest.py file provides fixtures for an entire directory.

pytest_plugins = [
    "tests.fixtures.api",
    "tests.fixtures.db",
    "tests.fixtures.doc",
    "tests.fixtures.doc_set",
    "tests.fixtures.prompt",
]

