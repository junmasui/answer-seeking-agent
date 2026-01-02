
import pytest
import asyncio
from backend.libs.core_db.tests.fixtures.db import *

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
