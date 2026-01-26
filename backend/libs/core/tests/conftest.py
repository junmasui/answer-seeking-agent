# Import fixture modules so pytest will register fixtures defined in them
# (for example: tests/fixtures/api.py defines `api_server`).

from libs.core.tests.fixtures.api import api_server, global_reset
from libs.core.tests.fixtures.db import (
    auto_mapped_classes,
    get_connection_str,
    reflected_metadata,
    sql_engine,
    sql_sessionmaker,
)
from libs.core.tests.fixtures.doc import (
    doc_table,
    empty_doc_table,
    ingested_doc_table,
    populated_doc_table,
)
from libs.core.tests.fixtures.doc_set import (
    doc_set_table,
    empty_doc_set_table,
    populated_doc_set_table,
    readonly_doc_set_table,
)
from libs.core.tests.fixtures.prompt import (
    empty_prompt_table,
    populated_prompt_table,
    prompt_table,
)
from libs.core.tests.fixtures.prompt_version import (
    empty_prompt_version_table,
    populated_prompt_version_table,
    prompt_version_table,
)
from libs.core.tests.fixtures.s3 import s3_bucket, s3_client
