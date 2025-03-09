from collections.abc import AsyncIterator, AsyncGenerator
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app import app, Device, Base
import pytest
import pytest_asyncio


DATABASE_URL = 'sqlite+aiosqlite:///:memory:'
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

@pytest_asyncio.fixture(scope='function')
async def test_transaction() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Create tables

    async with AsyncSessionLocal() as session:
        yield session

app.dependencies['transaction'] = lambda: AsyncSessionLocal()

TEST_CLIENT_ID = '1'


@pytest_asyncio.fixture(scope='function')
async def test_client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    async with AsyncTestClient(app=app) as client:
        yield client

async def create_device(session: AsyncSession, mac_address: str, username: str = 'j_doe', password: str = 'password', key: str = 'key', preferences: dict = None):
    if not preferences:
        preferences = {'preference_1': '1.0'}
    device = Device(
        mac_address=mac_address,
        username=username,
        password=password,
        key=key,
        preferences=preferences,
    )
    session.add(device)
    await session.commit()

@pytest.mark.asyncio
async def test_get_devices(test_client: AsyncTestClient[Litestar], test_transaction: AsyncSession) -> None:
    async with test_transaction as session:
        await create_device(session, '00:11:22:33:44:55')

    response = await test_client.get(f'/devices?client_id={TEST_CLIENT_ID}')
    print(response)