import asyncio
import logging
import time
from typing import AsyncGenerator
from urllib.parse import urljoin

import httpx
import pytest
import pytest_asyncio

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url

    async def _send(self, *, path: str, action, **kwargs):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                url = self.base_url
                if path:
                    url = urljoin(self.base_url, path)
                resp = await action(client, url, **kwargs)
        except httpx.ConnectError as ex:
            return 'exception', ex
        if resp.status_code != 200:
            logger.warning('error from API')
            return 'error', resp

        if resp.headers.get('content-type', None) != 'application/json':
            return 'success', resp

        return 'json', resp.json()

    async def get(self, *, path: str):
        """Send HTTP GET request."""

        async def _get(client, url):
            return await client.get(url)

        return await self._send(path=path, action=_get)

    async def delete(self, *, path: str):
        """Send HTTP DELETE request."""

        async def _delete(client, url):
            return await client.delete(url)

        return await self._send(path=path, action=_delete)

    async def patch(self, *, path: str, content_type: str, data: dict | list | str = None, files: dict = None):
        """Send HTTP PATCH request."""

        async def _patch(client, url):
            kwargs = {}
            match content_type:
                case 'json':
                    kwargs['json'] = data
                case 'multipart':
                    kwargs['data'] = data
                    if files is not None:
                        kwargs['files'] = files
                case _:
                    raise ValueError('Unknown content_type', content_type)
            return await client.patch(url, **kwargs)

        return await self._send(path=path, action=_patch)

    async def post(
        self, *, path: str, content_type: str, timeout=None, data: dict | list | str = None, files: dict = None
    ):
        """Send HTTP POST request."""

        async def _post(client, url):
            kwargs = {}
            if timeout is not None:
                kwargs['timeout'] = timeout
            match content_type:
                case 'json':
                    kwargs['json'] = data
                case 'multipart':
                    kwargs['data'] = data
                    if files is not None:
                        kwargs['files'] = files
                case None:
                    pass
                case _:
                    raise ValueError('Unknown content_type', content_type)
            return await client.post(url, **kwargs)

        return await self._send(path=path, action=_post)


@pytest_asyncio.fixture(loop_scope='module', scope='module')
async def api_server() -> AsyncGenerator[ApiClient, None]:
    # Wait (poll) for FastAPI to come on-line. "On-line" is later than the
    # process starting: it also means that start-up processing has completed.
    # Start-up processing includes pending database migrations, and ML model
    # downloads.
    start = time.time()
    delay = 1

    api_client = ApiClient('http://fastapi-integration-server:8100')
    while True:
        delta = time.time() - start
        if delta > 60:
            pytest.exit('API server not available')
        await asyncio.sleep(delay)

        status, content = await api_client.get(path='/')
        if status == 'json':
            break

        delay = min(delay + 1, 15)

    yield api_client


@pytest_asyncio.fixture(loop_scope='module', scope='module', autouse=True)
async def global_reset(api_server) -> AsyncGenerator[None, None]:
    path = '/admin/reset-database'
    logger.info('Resetting global state')
    resp = await api_server.post(path=path, content_type=None)

    yield

    logger.info('Resetting global state')
    resp = await api_server.post(path=path, content_type=None)
