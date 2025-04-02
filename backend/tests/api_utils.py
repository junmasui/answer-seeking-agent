import asyncio
import signal
import logging
import time

import pytest
import pytest_asyncio
import httpx

from global_config import get_global_config

logger = logging.getLogger(__name__)

@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def api_server():

    print('starting fastapi')

    # Start FastAPI as a subprocess
    process = await asyncio.create_subprocess_exec(
        "uvicorn", "core_app:app", "--host", "127.0.0.1", "--port", "8100"
    )

    # Wait (poll) for FastAPI to come on-line. "On-line" is later than the
    # process starting: it also means that start-up processing has completed.
    # Start-up processing includes pending database migrations, and ML model
    # downloads.
    start = time.time()
    delay = 1
    while True:
        delta = time.time() - start
        if delta > 60:
            pytest.exit("API server did not start")
        await asyncio.sleep(delay)

        try:
            async with httpx.AsyncClient() as client:
                r = await client.get('http://127.0.0.1:8100')
                if r.status_code == 200:
                    break
        except httpx.ConnectError as ex:
            pass

        delay = min( delay + 1, 15)
        


    yield {
        "port": "8100"
    }

    print('stopping fastapi')

    # Send a signal to cause program termination.
    process.send_signal(signal.SIGTERM)

    try:
        await asyncio.wait_for(process.wait(), timeout=60)
    except asyncio.TimeoutError:
        logger.info("Force terminating FastAPI process after timeout")
        process.kill()

    print('stopped fastapi')
