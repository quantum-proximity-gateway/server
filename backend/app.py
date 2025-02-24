from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler
from collections.abc import AsyncGenerator
from litestar import Litestar, get, post, put
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.config.cors import CORSConfig
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.exceptions import HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
import secrets, json
import urllib.parse
from typing import Annotated
from litestar.datastructures import UploadFile

import logging
import os


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

class FaceRegistrationRequest(BaseModel):
    mac_address: str
    video: UploadFile

    class Config(ConfigDict):
        arbitrary_types_allowed = True
    

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
async def register_device(data: RegisterDeviceRequest, transaction: AsyncSession) -> dict:
    query = select(Device).where(Device.mac_address == data.mac_address.strip())
    result = await transaction.execute(query)
    existing_device = result.scalar_one_or_none()

    if existing_device:
        raise HTTPException(status_code=409, detail='Device already registered')

    key = generate_key()
    device = Device(
        mac_address=data.mac_address.strip(),
        username=data.username,
        password=data.password,
        key=key,
        preferences='{}'
    )
    try:
        transaction.add(device)
    except:
        print('RAISE')
        raise HTTPException(status_code=400, detail='Device already registered')
    return {'status_code': 201, 'status': 'success', 'key': key}
    


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

@get('/devices/all-mac-addresses')
async def get_all_mac_addresses(transaction: AsyncSession) -> list[str]:
    query = select(Device.mac_address)
    result = await transaction.execute(query)
    mac_addresses = result.scalars().all()
    return mac_addresses

# Extracted the logic of the function to reuse elsewhere
async def fetch_username(mac_address: str, transaction: AsyncSession) -> str:
    mac_address = urllib.parse.unquote(mac_address)
    query = select(Device.username).where(Device.mac_address == mac_address)
    result = await transaction.execute(query)
    username = result.scalar_one_or_none()
    return username

@get('/devices/{mac_address:str}/username')
async def get_username(mac_address: str, transaction: AsyncSession) -> dict:
    username = await fetch_username(mac_address, transaction)
    if not username:
        return {'status_code': 404, 'detail': 'Device not found'}
    return {'username': username}

@get('/devices/{mac_address:str}/credentials') # TO BE CHANGED LATER TO USE validate_key() DEV PURPOSES ONLY
async def get_credentials(mac_address: str, transaction: AsyncSession) -> dict:
    mac_address = urllib.parse.unquote(mac_address)

    query = select(Device.username, Device.password).where(Device.mac_address == mac_address)

    result = await transaction.execute(query)
    credentials = result.one_or_none()
    print('Credentials:', credentials)
    if not credentials:
        return {'status_code': 404, 'detail': 'Device not found'}

    username, password = credentials
    return {'username': username, 'password': password}

@post('/registration/faceRec')
async def register_face(data: Annotated[FaceRegistrationRequest, Body(media_type=RequestEncodingType.MULTI_PART)], transaction: AsyncSession) -> dict:
    mac_address = data.mac_address
    logging.info(f"Received mac_address: {mac_address}")
    video = await data.video.read()

    username = await fetch_username(mac_address, transaction) # To be used as folder name
    script_dir = os.path.dirname(__file__)  # Get the directory of the current script
    video_path = os.path.join(script_dir, "videos", username, 'video.webm')

    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    with open(video_path, 'wb') as video_file:
        video_file.write(video)
    
    return {'status': 'success', 'video_path': video_path}
 
    # Upload frames to GitHub: Create folder under username, upload folder to rpi-code repo


    # Somehow automate retraining - continous git pulls? - To be implemented on rpi-code



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
        update_preferences,
        get_all_mac_addresses,
        get_username,
        get_credentials,
        register_face,
    ],
    dependencies={'transaction': provide_transaction},
    plugins=[sqlalchemy_plugin],
    cors_config=cors_config,
    debug=True
)
