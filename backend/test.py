from collections.abc import AsyncIterator
from litestar import Litestar
from litestar.testing import AsyncTestClient
from app import app, encryption_helper
import pytest
import pytest_asyncio
import os


TEST_DB_FILENAME = 'test_db.sqlite'
if os.path.isfile(TEST_DB_FILENAME):
    os.remove(TEST_DB_FILENAME)

TEST_CLIENT_ID = '1'
TEST_SHARED_SECRET = b'\xbd\xb4\xe9\xf7\x91\xf3\x97\x90\xc1\x93i\xe2\xc9\x0b\xa3\x115\xac\xcb<\xae\x96\xd6\x16\x88\x18\xc8\xd9FRG?'
encryption_helper.shared_secrets[TEST_CLIENT_ID] = TEST_SHARED_SECRET


@pytest_asyncio.fixture(scope='function')
async def test_client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    async with AsyncTestClient(app=app) as client:
        yield client

