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


class ValidateKeyRequest(BaseModel):
    mac_address: str
    key: str


class RegenerateKeyRequest(BaseModel):
    mac_address: str


class GetPreferencesRequest(BaseModel):
    mac_address: str


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

@post('/devices/validate-key')
async def validate_key(data: ValidateKeyRequest, transaction: AsyncSession) -> dict:
    query = select(Device).where(Device.mac_address == data.mac_address)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        return {'status_code': 404, 'detail': 'Device not found'}
    
    if device.key != data.key:
        return {'status_code': 401, 'detail': 'Invalid key'}
    
    new_key = generate_key()
    device.key = new_key
    return {'status': 'success'}

@post('/devices/regenerate-key')
async def regenerate_key(data: RegenerateKeyRequest, transaction: AsyncSession) -> dict:
    query = select(Device).where(Device.mac_address == data.mac_address)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        return {'status_code': 404, 'detail': 'Device not found'}

    new_key = generate_key()
    device.key = new_key
    return {'status': 'success'}

@get('/devices/{mac_address}/preferences')
async def get_preferences(data: GetPreferencesRequest, transaction: AsyncSession) -> dict:
    query = select(Device).where(Device.mac_address == data.mac_address)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        return {'status_code': 404, 'detail': 'Device not found'}
    
    return {'preferences': device.preferences}

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
        register_device,
        validate_key,
        regenerate_key,
        get_preferences
    ],
    dependencies={'transaction': provide_transaction},
    plugins=[sqlalchemy_plugin],
    debug=True
)