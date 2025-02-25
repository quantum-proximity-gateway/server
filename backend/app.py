import secrets
import json
import urllib.parse
import logging
import os
import cv2
import subprocess
import shutil
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
from typing import Annotated
from litestar.datastructures import UploadFile
from github import Github
from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = 'devices'

    mac_address: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str]
    password: Mapped[str]
    key: Mapped[str]
    preferences: Mapped[dict]


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

class UpdateJSONPreferencesRequest(BaseModel):
    username: str
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

    def convert_to_mp4(webm_path: str, mp4_path: str) -> None:
        """Convert a WebM file to MP4 using ffmpeg."""
        # Common options: -c:v libx264 for video, -c:a aac for audio.
        # Adjust as needed for your environment/codecs.
        command = [
            'ffmpeg',
            '-i', webm_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-strict', 'experimental',  # Sometimes needed for aac
            '-y',  # Overwrite without asking
            mp4_path
        ]
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            logging.error(f"FFmpeg conversion failed: {e.stderr.decode('utf-8', errors='replace')}")
            raise HTTPException(status_code=500, detail="Failed to convert WebM to MP4")

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
    
    # Grab 5 frames from the video
    cap = cv2.VideoCapture(mp4_path)

    if not cap.isOpened():
        logging.error("Error opening video file")
        return {'status': 'error', 'detail': 'Error opening video file'}
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps else 0
    skip_frames = int(0.5 * fps) # skip first 0.5 seconds - camera stabilization

    logging.info(f"Video info - FPS: {fps}, Total frames: {total_frames}, Duration: {duration_sec:.2f}s")

    # not really necessary - but just in case
    if duration_sec < 2: 
        logging.warning("Video duration is shorter than 2 seconds—check the frontend code or device recording.")
    if (total_frames - skip_frames) < 5:
        logging.error("Video too short")
        return {'status': 'error', 'detail': 'Video too short'}

    interval = max(1, (total_frames - skip_frames) // 6)

    frames_dir = os.path.join(user_video_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    extracted_frames = []
    for i in range(1, 6):
        
        frame_idx = skip_frames + i * interval
        if frame_idx >= total_frames: # in case of rounding / video shorter than expected
            break
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret or frame is None:
            logging.warning(f"Error reading frame {i}")
            continue
        
        frame_path = os.path.join(frames_dir, f'frame_{i}.jpg')
        cv2.imwrite(frame_path, frame)
        extracted_frames.append(frame_path)
        logging.info(f"Saved frame {i} to {frame_path}")

    cap.release()

    # Upload frames to GitHub: Create folder under username, upload folder to rpi-code repo
    github_token = os.getenv('GITHUB_AUTH_TOKEN')
    if not github_token:
        logging.error("GitHub token not found")
        return {'status': 'error', 'detail': 'GitHub token not found'}
    
    try:
        g = Github(github_token)
        repo = g.get_repo("quantum-proximity-gateway/rpi-code")

        for frame_file in extracted_frames:
            with open(frame_file, 'rb') as frame:
                content = frame.read()

            file_name = os.path.basename(frame_file)
            remote_path = f"main/dataset/{username}/{file_name}"

            try:
                existing_file = repo.get_contents(remote_path)
                logging.info(f"File {file_name} already exists")

                repo.update_file(
                    path=remote_path,
                    message=f"Update {remote_path}",
                    content=content,
                    sha=existing_file.sha
                )
                logging.info(f"Updated file in GitHub: {remote_path}")
            
            except Exception as e:
                logging.info(f"File {file_name} not found, creating new file")
                repo.create_file(
                    path=remote_path,
                    message=f"Add {remote_path}",
                    content=content
                )
                logging.info(f"Uploaded file to GitHub: {remote_path}")
        
    except Exception as e:
        logging.error(f"Error uploading frames to GitHub: {e}")
        return {'status': 'error', 'detail': 'Error uploading frames'}

    if os.path.exists(user_video_dir):
        shutil.rmtree(user_video_dir, ignore_errors=True)
        logging.info(f"Deleted folder: {user_video_dir}")

    return {'status': 'success', 'video_path': video_path}

    #TODO: 2.0
    # Somehow automate retraining - continous git pulls? - To be implemented on rpi-code

@post('/preferences/update')
async def update_json_preferences(data: UpdateJSONPreferencesRequest, transaction: AsyncSession) -> dict:
    query = select(Device).where(Device.username == data.username)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        return {'status_code': 404, 'detail': 'Device not found'}

    device.preferences = json.dumps(data.preferences)
    return {'status': 'success', 'preferences': data.preferences}

@get('/preferences/{username:str}')
async def get_json_preferences(username: str, transaction: AsyncSession) -> dict:
    query = select(Device).where(Device.username == username)
    result = await transaction.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        return {'status_code': 404, 'detail': 'Device not found'}
    
    try:
        parsed_preferences = json.loads(device.preferences)
        return {'preferences': parsed_preferences}
    except json.JSONDecodeError:
        return {'status_code': 500, 'detail': 'Stored preferences are not valid JSON'}


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
