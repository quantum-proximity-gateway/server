import requests
import oqs
import base64
from aesgcm_encryption import aesgcm_encrypt, aesgcm_decrypt
import uuid
from pydantic import BaseModel

CLIENT_ID = str(uuid.uuid4())
KEM_ALGORITHM = 'Kyber512'
SERVER_URL = 'http://127.0.0.1:8000'  # Bug with urllib3, so using http instead of https

class KEMException(Exception):
    pass

class EncryptedResponse(BaseModel):
    nonce_b64: str
    ciphertext_b64: str

def generate_shared_secret() -> bytes:
    '''
    Initiates and completes a key exchange in order to create a shared secret.
    '''
    
    # Get public key
    data = {'client_id': str(CLIENT_ID)}
    response = requests.post(f'{SERVER_URL}/kem/initiate', json=data)
    public_key_b64 = response.json().get('public_key_b64')
    if not public_key_b64:
        raise KEMException('Public key not found in response.')

    # Encapsulate a shared secret
    with oqs.KeyEncapsulation(KEM_ALGORITHM) as client_kem:
        try:
            public_key = base64.b64decode(public_key_b64)
            ciphertext, shared_secret = client_kem.encap_secret(public_key)
        except Exception as e:
            raise KEMException('Invalid public key, could not encapsulate secret.')

    # Send encapsulated shared secret
    ciphertext_b64 = base64.b64encode(ciphertext).decode()
    data = {'client_id': str(CLIENT_ID), 'ciphertext_b64': ciphertext_b64}
    response = requests.post(f'{SERVER_URL}/kem/complete', json=data)
    if response.status_code != 201:
        raise KEMException(f'Unexpected status code: {response.status_code}.')
    
    return shared_secret

def encrypt_request(plaintext: str, shared_secret: bytes) -> dict:
    nonce_b64, ciphertext_b64 = aesgcm_encrypt(plaintext, shared_secret)

    data = {
        'client_id': str(CLIENT_ID),
        'nonce_b64': nonce_b64,
        'ciphertext_b64': ciphertext_b64
    }

    return data

def decrypt_request(data: EncryptedResponse, shared_secret) -> dict: # pass in response.json()
    if not data.nonce_b64 or not data.ciphertext_b64:
        raise RuntimeError('Missing parameters in response.')
    
    try:
        plaintext = aesgcm_decrypt(data.nonce_b64, data.ciphertext_b64, shared_secret)
        return plaintext
    except Exception as e:
        raise RuntimeError(f'Error: {e}\nFailed to decrypt response data.')


if __name__ == '__main__':
    # Example usage
    
    # Generate shared secret (generate once, use whenever communicating between this client and server)
    try:
        shared_secret = generate_shared_secret()
    except KEMException as e:
        raise RuntimeError(f'KEM failed, could not generate secret: {e}')
    # Encrypt request data
    request_text = 'Hello, Litestar!'
    data = encrypt_request(request_text, shared_secret)

    response = requests.post(f'{SERVER_URL}/example-endpoint', json=data)

    if response.status_code != 201:
        raise RuntimeError(f'Error {response.status_code}: {response.text}')
    
    response_data = response.json()
    encrypted_response = EncryptedResponse.model_validate(response_data)
    print(response_data)
    server_response = decrypt_request(encrypted_response, shared_secret)
    print(server_response)
    