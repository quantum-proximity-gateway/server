from collections.abc import AsyncIterator
from litestar import Litestar
from litestar.testing import AsyncTestClient
from . import app
import pytest


app.debug = True


@pytest.fixture(scope="function")
async def test_client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    with AsyncTestClient(app=app) as client:
        yield client