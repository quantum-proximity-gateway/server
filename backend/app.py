from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler
from collections.abc import AsyncGenerator
from litestar import Litestar, get, post
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
import secrets


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = 'devices'

    mac_address: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str]
    password: Mapped[str]
    key: Mapped[str]
    preferences: Mapped[str]


class RegisterDeviceRequest(BaseModel):
    mac_address: str
    username: str
    password: str


def generate_key(length: int = 32) -> str:
    return ''.join(secrets.choice([chr(i) for i in range(0x21, 0x7F)]) for _ in range(length))

async def provide_transaction(db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    async with db_session.begin():
        yield db_session

@get('/devices')
async def get_devices(transaction: AsyncSession) -> list[Device]:
    query = select(Device)
    result = await transaction.execute(query)
    devices = result.scalars().all()
    return devices

@post('/devices')
async def register_device(data: RegisterDeviceRequest, transaction: AsyncSession) -> Device:
    key = generate_key()
    device = Device(
        mac_address=data.mac_address,
        username=data.username,
        password=data.password,
        key=key,
        preferences='{}'
    )
    transaction.add(device)
    return device

# validate key

# regenerate key

# retrieve preferences for device

# update preferences for device


db_config = SQLAlchemyAsyncConfig(
    connection_string='sqlite+aiosqlite:///db.sqlite',
    metadata=Base.metadata,
    create_all=True,
    before_send_handler=autocommit_before_send_handler
)
sqlalchemy_plugin = SQLAlchemyPlugin(config=db_config)

app = Litestar(
    route_handlers=[
        get_devices,
        register_device
    ],
    dependencies={'transaction': provide_transaction},
    plugins=[sqlalchemy_plugin],
    debug=True
)