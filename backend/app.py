import json
import urllib.parse
import logging
import os
import shutil
import time
import hmac
import pickle
import hashlib
import numpy as np
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler
from collections.abc import AsyncGenerator
from litestar import Litestar, get, post, Request, put
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin
from litestar.config.cors import CORSConfig
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.exceptions import HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import JSON
from typing import Annotated, Any
from litestar.datastructures import UploadFile
from github import Github, GithubException
from dotenv import load_dotenv
from copy import deepcopy
from encryption_helper import EncryptionHelper
from video_encoding import convert_to_mp4, split_frames
from train_model import train_model

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

json_path = os.path.join(os.path.dirname(__file__), 'json_example.json')
with open(json_path, 'r') as f:
    DEFAULT_PREFS = json.load(f)

encryption_helper = EncryptionHelper()


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = 'devices'

    mac_address: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str]
    password: Mapped[str]
    secret: Mapped[str] # Shared secret used in TOTP, maybe encrypt?
    totp_timestamp: Mapped[int]
    preferences: Mapped[MutableDict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=lambda: deepcopy(DEFAULT_PREFS),
        nullable=False
    )


class RegisterDeviceRequest(BaseModel):
    mac_address: str
    username: str
    password: str
    secret: str
    timestamp: int

class EncryptedMessageRequest(BaseModel):
    client_id: str
    nonce_b64: str
    ciphertext_b64: str

class UpdatePreferencesRequest(BaseModel):
    preferences: dict


class KEMInitiateRequest(BaseModel):
    client_id: str


class KEMCompleteRequest(BaseModel):
    client_id: str
    ciphertext_b64: str


class FaceRegistrationRequest(BaseModel):
    mac_address: str
    video: UploadFile

    class Config(ConfigDict):
        arbitrary_types_allowed = True

class UpdateJSONPreferencesRequest(BaseModel):
    username: str
    preferences: dict

class CredentialsRequest(BaseModel):
    mac_address: str
    totp: int

async def generate_totp(mac_address: str ,transaction: AsyncSession) -> int:
    query = select(Device.secret, Device.totp_timestamp).where(Device.mac_address == mac_address)
    result = await transaction.execute(query)
    results = result.one_or_none()
    if not results:
        raise HTTPException(status_code=404, detail='Device not found')
    secret, timestamp = results
    return totp(secret, timestamp)


def totp(secret: str, timestamp: int) -> int:
    time_now = time.time()
    time_elapsed = int(time_now - timestamp)
    TOTP_DIGITS = 6
    TIME_STEP = 30
    time_counter = int(time_elapsed / TIME_STEP)
    counter = [None] * 8

    # convert to 8 byte array
    for i in range(7, -1, -1):
        counter[i] = time_counter & 0xFF
        time_counter >>= 8

    h = hmac.new(bytes(secret.encode()), bytes(counter), hashlib.sha1)
    hmac_digest = h.digest()
    offset = hmac_digest[19] & 0x0F
    bin_code = ((hmac_digest[offset] & 0x7F) << 24 |
                ((hmac_digest[offset + 1] & 0xFF) << 16) |
                ((hmac_digest[offset + 2] & 0xFF) << 8) |
                (hmac_digest[offset + 3] & 0xFF))
    
    mod_divisor = 1
    for i in range(TOTP_DIGITS):
        mod_divisor *= 10
    totp_code = bin_code % mod_divisor
    return totp_code

async def provide_transaction(db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    async with db_session.begin():
        yield db_session

async def fetch_username(mac_address: str, transaction: AsyncSession) -> str:
    mac_address = urllib.parse.unquote(mac_address)
    query = select(Device.username).where(Device.mac_address == mac_address)
    result = await transaction.execute(query)
    username = result.scalar_one_or_none()
    return username

@get('/devices')
async def get_devices(request: Request, transaction: AsyncSession) -> dict:
    client_id = request.query_params.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id query parameter is required')
    
    query = select(Device)
    result = await transaction.execute(query)
    devices = result.scalars().all()

    serialized_devices = [device.__dict__ for device in devices]
    for device in serialized_devices:
        device.pop('_sa_instance_state', None)
    
    return encryption_helper.encrypt_msg({'devices': serialized_devices}, client_id)

@post('/register')
async def register_device(data: EncryptedMessageRequest, transaction: AsyncSession) -> None:
    if not data.client_id:
        raise HTTPException(status_code=400, detail='client_id parameter is required')
    client_id = data.client_id
    decrypted_data = encryption_helper.decrypt_msg(data)
    validated_data = RegisterDeviceRequest(**decrypted_data)

    query = select(Device).where(Device.mac_address == validated_data.mac_address.strip())
    result = await transaction.execute(query)
    existing_device = result.scalar_one_or_none()

    if existing_device:
        raise HTTPException(status_code=409, detail='Device already registered')
    
    # TODO: Need to think of a way to encrypt the password on the db

    device = Device(
        mac_address=validated_data.mac_address.strip(),
        username=validated_data.username,
        password=validated_data.password,
        secret=validated_data.secret,
        totp_timestamp= int(validated_data.timestamp/1000) # JavaScript Date.now() uses ms
    )
    try:
        transaction.add(device)
    except:
        print('RAISE')
        raise HTTPException(status_code=400, detail='Device already registered')
    return encryption_helper.encrypt_msg({'status_code': 201, 'status': 'success'}, client_id)


@get('/devices/{mac_address:str}/preferences')
async def get_preferences(request: Request, mac_address: str, transaction: AsyncSession) -> dict:
    client_id = request.query_params.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id query parameter is required')

    query = select(Device).where(Device.mac_address == mac_address)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail='Device not found')
    
    try:
        parsed_preferences = json.loads(device.preferences)
        return encryption_helper.encrypt_msg({'preferences': parsed_preferences}, client_id)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail='Preferences are not a valid JSON')


@put('/devices/{mac_address:str}/preferences')
async def update_preferences(mac_address: str, data: EncryptedMessageRequest, transaction: AsyncSession) -> dict:
    if not data.client_id:
        raise HTTPException(status_code=400, detail='client_id parameter is required')
    decryped_data = encryption_helper.decrypt_msg(data)
    validated_data = UpdatePreferencesRequest(**decryped_data)
    query = select(Device).where(Device.mac_address == mac_address)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail='Device not found')

    return encryption_helper.encrypt_msg({'status': 'success', 'preferences': validated_data.preferences}, data.client_id)

@get('/devices/all-mac-addresses')
async def get_all_mac_addresses(request: Request, transaction: AsyncSession) -> list[str]:
    client_id = request.query_params.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id query parameter is required')

    query = select(Device.mac_address)
    result = await transaction.execute(query)
    mac_addresses = result.scalars().all()
    return encryption_helper.encrypt_msg({"mac_addresses": mac_addresses}, client_id)

@get('/devices/{mac_address:str}/username')
async def get_username(request: Request, mac_address: str, transaction: AsyncSession) -> dict:
    client_id = request.query_params.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id query parameter is required')
    
    username = await fetch_username(mac_address, transaction)
    if not username:
        raise HTTPException(status_code=404, detail='Device not found')
    return encryption_helper.encrypt_msg({'username': username}, client_id)

@put('/devices/credentials') 
async def get_credentials(data: EncryptedMessageRequest, transaction: AsyncSession) -> dict:    
    decrypted_data = encryption_helper.decrypt_msg(data)
    validated_data = CredentialsRequest(**decrypted_data)
    check_totp = await generate_totp(validated_data.mac_address, transaction)
    if validated_data.totp == check_totp:
        query = select(Device.username, Device.password).where(Device.mac_address == validated_data.mac_address)

        result = await transaction.execute(query)
        credentials = result.one_or_none()
        if not credentials:
            raise HTTPException(status_code=404, detail="Device not found.")

        username, password = credentials
        credential_data = {'username': username, 'password': password}
        encrypted_data = encryption_helper.encrypt_msg(credential_data, data.client_id)
        return encrypted_data
    else:
        print("Generated:", check_totp)
        print("Received TOTP:", validated_data.totp)
        raise HTTPException(status_code=500, detail='TOTP does not match')


@post('/preferences/update')
async def update_json_preferences(data: EncryptedMessageRequest, transaction: AsyncSession) -> dict:
    client_id = data.client_id
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id query parameter is required')

    decrypted_data = encryption_helper.decrypt_msg(data)
    validated_data = UpdateJSONPreferencesRequest(**decrypted_data)

    query = select(Device).where(Device.username == validated_data.username)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail='Device not found')

    try:
        device.preferences = validated_data.preferences
        await transaction.commit()
        return encryption_helper.encrypt_msg({'preferences': validated_data.preferences}, client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail='Failed to update preferences')

@get('/preferences/{username:str}')
async def get_json_preferences(request: Request, username: str, transaction: AsyncSession) -> dict:
    client_id = request.query_params.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id query parameter is required')
    
    query = select(Device).where(Device.username == username)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail='Username not found')
    
    try:
        parsed_preferences = device.preferences
        return encryption_helper.encrypt_msg({'preferences': parsed_preferences},client_id)
    except Exception as e:
       raise HTTPException(status_code=500, detail='Preferences are not a valid JSON')

@get('/encodings')
async def get_encodings(request: Request) -> dict:
    client_id = request.query_params.get('client_id')
    if not client_id:
        raise HTTPException(status_code=400, detail='client_id query parameter is required')
    
    pickle_file_path = "encodings.pickle"
    if not os.path.exists(pickle_file_path):
        return encryption_helper.encrypt_msg({}, client_id)

    with open(pickle_file_path, 'rb') as f:
        data = pickle.load(f)

    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(i) for i in obj]
        else:
            return obj

    serializable_data = convert_to_serializable(data)

    return encryption_helper.encrypt_msg(serializable_data, client_id)

class KEMInitiateRequest(BaseModel):
    client_id: str

class KEMCompleteRequest(BaseModel):
    client_id: str
    ciphertext_b64: str

@post('/kem/initiate')
async def kem_initiate(data: KEMInitiateRequest) -> dict:
    return encryption_helper.kem_initiate(data)

@post('/kem/complete')
async def kem_complete(data: KEMCompleteRequest) -> dict:
    return encryption_helper.kem_complete(data)

@post('/register/face')
async def register_face(data: Annotated[FaceRegistrationRequest, Body(media_type=RequestEncodingType.MULTI_PART)], transaction: AsyncSession) -> dict:
    mac_address = data.mac_address
    logging.info(f"Received mac_address: {mac_address}")
    #TODO: Add check to see if face already registered
    username = await fetch_username(mac_address, transaction) # To be used as folder name
    script_dir = os.path.dirname(__file__)  # Get the directory of the current script
    user_video_dir = os.path.join(script_dir, "videos", username)
    video_path = os.path.join(user_video_dir, 'video.webm')

    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    chunk_size = 1024 * 1024 # 1MB
    with open(video_path, 'wb') as video_file:
        while True:
            chunk = await data.video.read(chunk_size)
            if not chunk:
                break
            video_file.write(chunk)

    # need to convert to mp4 cuz webm isn't fully saved/processed by the time we need to extract frames
    mp4_path = os.path.join(user_video_dir, "video.mp4")
    convert_to_mp4(video_path, mp4_path)
    extracted_frames = split_frames(mp4_path, user_video_dir)
    print(extracted_frames)
    # retrain model on new frames, might need to async it
    train_model(extracted_frames, username)

    # delete folder
    if os.path.exists(user_video_dir):
        shutil.rmtree(user_video_dir, ignore_errors=True)
        logging.info(f"Deleted folder: {user_video_dir}")

    return {'status': 'success'}

TEST = False
if TEST:
    filename = 'test_db.sqlite'
else:
    filename = 'db.sqlite'

db_config = SQLAlchemyAsyncConfig(
    connection_string=f'sqlite+aiosqlite:///{filename}',
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
        register_device,
        get_preferences,
        update_preferences,
        get_all_mac_addresses,
        get_username,
        get_credentials,
        register_face,
        get_json_preferences,
        update_json_preferences,
        kem_complete,
        kem_initiate,
        get_encodings
    ],
    dependencies={'transaction': provide_transaction},
    plugins=[sqlalchemy_plugin],
    cors_config=cors_config,
    debug=True
)
