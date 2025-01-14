from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler
from collections.abc import AsyncGenerator
from litestar import Litestar, get, post, put
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.config.cors import CORSConfig
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
import secrets, json


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


class UpdatePreferencesRequest(BaseModel):
    preferences: dict


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


@post('/register')
async def register_device(data: RegisterDeviceRequest, transaction: AsyncSession) -> Device:
    key = generate_key()
    print(key)
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


@get('/devices/{mac_address:str}/preferences')
async def get_preferences(mac_address: str, transaction: AsyncSession) -> dict:
    query = select(Device).where(Device.mac_address == mac_address)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        return {'status_code': 404, 'detail': 'Device not found'}
    
    try:
        parsed_preferences = json.loads(device.preferences)
        return {'preferences': parsed_preferences}
    except json.JSONDecodeError:
        return {'status_code': 500, 'detail': 'Stored preferences are not valid JSON'}


@put('/devices/{mac_address:str}/preferences')
async def update_preferences(mac_address: str, data: UpdatePreferencesRequest, transaction: AsyncSession) -> dict:
    query = select(Device).where(Device.mac_address == mac_address)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        return {'status_code': 404, 'detail': 'Device not found'}

    device.preferences = json.dumps(data.preferences)
    return {'status': 'success', 'preferences': data.preferences}


db_config = SQLAlchemyAsyncConfig(
    connection_string='sqlite+aiosqlite:///db.sqlite',
    metadata=Base.metadata,
    create_all=True,
    before_send_handler=autocommit_before_send_handler
)
sqlalchemy_plugin = SQLAlchemyPlugin(config=db_config)

cors_config = CORSConfig(
    allow_origins=['*'], 
    allow_methods=['GET', 'POST', 'PUT'],  # Allow specific HTTP methods
    allow_headers=['*']
)

app = Litestar(
    route_handlers=[
        get_devices,
        register_device,
        validate_key,
        regenerate_key,
        get_preferences,
        update_preferences
    ],
    dependencies={'transaction': provide_transaction},
    plugins=[sqlalchemy_plugin],
    cors_config=cors_config,
    debug=True
)