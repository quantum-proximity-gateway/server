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
    preferences: str = '{}'


def generate_key(length: int = 32) -> str:
    return ''.join(secrets.choice([chr(i) for i in range(0x21, 0x7F)]) for _ in range(length))

@get('/devices')
async def get_devices(db_session: AsyncSession) -> list[Device]:
    query = select(Device)
    result = await db_session.execute(query)
    devices = result.scalars().all()
    return devices

@post('/devices')
async def register_device(data: RegisterDeviceRequest, db_session: AsyncSession) -> Device:
    key = generate_key()

    device = Device(
        mac_address=data.mac_address,
        username=data.username,
        password=data.password,
        key=key,
        preferences=data.preferences
    )

    db_session.add(device)
    await db_session.commit()

    return device

# validate key

# regenerate key

# retrieve preferences for device

# update preferences for device

db_config = SQLAlchemyAsyncConfig(
    connection_string='sqlite+aiosqlite:///db.sqlite',
    metadata=Base.metadata,
    create_all=True
)
sqlalchemy_plugin = SQLAlchemyPlugin(config=db_config)

app = Litestar(
    route_handlers=[
        get_devices,
        register_device
    ],
    plugins=[sqlalchemy_plugin],
    debug=True
)