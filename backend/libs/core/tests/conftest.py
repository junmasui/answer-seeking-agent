import os
import sys

# Add the libs/core directory to sys.path so tests.fixtures can be imported
libs_core_dir = os.path.dirname(os.path.dirname(__file__))
if libs_core_dir not in sys.path:
    sys.path.append(libs_core_dir)

pytest_plugins = [
    "tests.fixtures.api",
    "tests.fixtures.db",
    "tests.fixtures.doc",
    "tests.fixtures.doc_set",
    "tests.fixtures.prompt",
    "tests.fixtures.prompt_version",
    "tests.fixtures.s3",
]

