from collections.abc import AsyncIterator
from litestar import Litestar
from litestar.testing import AsyncTestClient
from app import app, encryption_helper
import pytest
import pytest_asyncio


TEST_CLIENT_ID = '1'
TEST_SHARED_SECRET = b'\xbd\xb4\xe9\xf7\x91\xf3\x97\x90\xc1\x93i\xe2\xc9\x0b\xa3\x115\xac\xcb<\xae\x96\xd6\x16\x88\x18\xc8\xd9FRG?'
encryption_helper.shared_secrets[TEST_CLIENT_ID] = TEST_SHARED_SECRET


@pytest_asyncio.fixture(scope='function')
async def test_client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    async with AsyncTestClient(app=app) as client:
        yield client

@pytest.mark.asyncio
async def test_get_devices(test_client: AsyncTestClient[Litestar]) -> None:
    {'mac_address': '00:11:22:33:44:55', 'username': 'jdoe', 'password': 'password'}
    await test_client.post('/register')

    response = await test_client.get(f'/devices?client_id={TEST_CLIENT_ID}')
    print(response)