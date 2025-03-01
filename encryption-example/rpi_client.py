import requests
import oqs
import base64
from aesgcm_encryption import aesgcm_encrypt, aesgcm_decrypt

CLIENT_ID = 42
KEM_ALGORITHM = 'Kyber512'
SERVER_URL = 'http://127.0.0.1:8000'  # Bug with urllib3, so using http instead of https


class KEMException(Exception):
    pass


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

if __name__ == '__main__':
    # Example usage

    # Generate shared secret
    try:
        shared_secret = generate_shared_secret()
    except KEMException as e:
        raise RuntimeError(f'KEM failed, could not generate secret: {e}')

    # Encrypt request data
    request_text = 'Hello, Litestar!'
    nonce_b64, ciphertext_b64 = aesgcm_encrypt(request_text, shared_secret)

    # POST request
    data = {
        'client_id': str(CLIENT_ID),
        'nonce_b64': nonce_b64,
        'ciphertext_b64': ciphertext_b64
    }
    response = requests.post(f'{SERVER_URL}/example-endpoint', json=data)

    if response.status_code != 201:
        raise RuntimeError(f'Error {response.status_code}: {response.text}')
    
    response_data = response.json()
    nonce_b64 = response_data.get('nonce_b64')
    ciphertext_b64 = response_data.get('ciphertext_b64')
    if not nonce_b64 or not ciphertext_b64:
        raise RuntimeError('Missing parameters in response.')

    # Decrypt response data
    try:
        plaintext = aesgcm_decrypt(nonce_b64, ciphertext_b64, shared_secret)
        print(f'Client received: {plaintext}')
    except Exception as e:
        raise RuntimeError(f'Error: {e}\nFailed to decrypt response data.')