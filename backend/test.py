from collections.abc import AsyncIterator
from litestar import Litestar
from litestar.testing import AsyncTestClient
from app import app, encryption_helper, EncryptedMessageRequest
import pytest
import pytest_asyncio
import os


TEST_DB_FILENAME = 'test_db.sqlite'

TEST_CLIENT_ID_1 = '1'
TEST_SHARED_SECRET_1 = b'\xbd\xb4\xe9\xf7\x91\xf3\x97\x90\xc1\x93i\xe2\xc9\x0b\xa3\x115\xac\xcb<\xae\x96\xd6\x16\x88\x18\xc8\xd9FRG?'
encryption_helper.shared_secrets[TEST_CLIENT_ID_1] = TEST_SHARED_SECRET_1

TEST_CLIENT_ID_2 = '2'
TEST_SHARED_SECRET_2 = b'\xbd\xb3\xe9\xf7\x91\xf3\x97\x90\xc1\x93i\xe2\xc9\x0b\xa3\x115\xac\xcb<\xae\x96\xd6\x16\x88\x18\xc8\xd9FRG?'
encryption_helper.shared_secrets[TEST_CLIENT_ID_2] = TEST_SHARED_SECRET_2


@pytest_asyncio.fixture(scope='function')
async def test_client() -> AsyncIterator[AsyncTestClient[Litestar]]:
    # Delete test database, if it exists, before next test 
    if os.path.isfile(TEST_DB_FILENAME):
        os.remove(TEST_DB_FILENAME)

    async with AsyncTestClient(app=app) as client:
        yield client

@pytest.mark.asyncio
async def test_get_devices(test_client: AsyncTestClient[Litestar]) -> None:
    # Ensure no devices are returned when none have been registered yet
    response = await test_client.get(f'/devices?client_id={TEST_CLIENT_ID_1}')
    response_data = encryption_helper.decrypt_msg(EncryptedMessageRequest(**({'client_id': TEST_CLIENT_ID_1} | response.json())))
    assert len(response_data['devices']) == 0

    # Test that one device is returned when a device has been registered
    data = {
        'mac_address': '00:11:22:33:44:55',
        'username': 'john_doe',
        'password': 'password'
    }
    encrypted_data = {'client_id': TEST_CLIENT_ID_1} | encryption_helper.encrypt_msg(data, TEST_CLIENT_ID_1)
    _ = await test_client.post('/register', json=encrypted_data)

    response = await test_client.get(f'/devices?client_id={TEST_CLIENT_ID_1}')
    response_data = encryption_helper.decrypt_msg(EncryptedMessageRequest(**({'client_id': TEST_CLIENT_ID_1} | response.json())))
    assert len(response_data['devices']) == 1

    # Test that two devices are returned when two devices have been registered
    data = {
        'mac_address': '11:22:33:44:55:66',
        'username': 'j.doe',
        'password': 'password'
    }
    encrypted_data = {'client_id': TEST_CLIENT_ID_2} | encryption_helper.encrypt_msg(data, TEST_CLIENT_ID_2)
    _ = await test_client.post('/register', json=encrypted_data)

    response = await test_client.get(f'/devices?client_id={TEST_CLIENT_ID_2}')
    response_data = encryption_helper.decrypt_msg(EncryptedMessageRequest(**({'client_id': TEST_CLIENT_ID_2} | response.json())))
    assert len(response_data['devices']) == 2

@pytest.mark.asyncio
async def test_register_device(test_client: AsyncTestClient) -> None:
    # Test registering a new device
    data = {
        'mac_address': '00:11:22:33:44:55',
        'username': 'john_doe',
        'password': 'password'
    }
    encrypted_data = {'client_id': TEST_CLIENT_ID_1} | encryption_helper.encrypt_msg(data, TEST_CLIENT_ID_1)
    response = await test_client.post('/register', json=encrypted_data)
    assert response.status_code == 201

    # Test registering the same device again (should fail)
    response = await test_client.post('/register', json=encrypted_data)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_get_all_mac_addresses(test_client: AsyncTestClient) -> None:
    # Register a device
    data = {
        'mac_address': '00:11:22:33:44:55',
        'username': 'john_doe',
        'password': 'password'
    }
    encrypted_data = {'client_id': TEST_CLIENT_ID_1} | encryption_helper.encrypt_msg(data, TEST_CLIENT_ID_1)
    _ = await test_client.post('/register', json=encrypted_data)

    data = {
        'mac_address': '11:22:33:44:55:66',
        'username': 'j.doe',
        'password': 'password'
    }
    encrypted_data = {'client_id': TEST_CLIENT_ID_2} | encryption_helper.encrypt_msg(data, TEST_CLIENT_ID_2)
    _ = await test_client.post('/register', json=encrypted_data)

    # Fetch all MAC addresses
    response = await test_client.get(f'/devices/all-mac-addresses?client_id={TEST_CLIENT_ID_1}')
    response_data = encryption_helper.decrypt_msg(EncryptedMessageRequest(**({'client_id': TEST_CLIENT_ID_1} | response.json())))
    assert set(response_data['mac_addresses']) == set(['00:11:22:33:44:55', '11:22:33:44:55:66'])