import requests
import oqs
import base64
from aesgcm_encryption import aesgcm_encrypt, aesgcm_decrypt

CLIENT_ID = 42
KEM_ALGORITHM = 'Kyber512'
SERVER_URL = 'http://127.0.0.1:8000' # Bug with urllib3, so using http instead of https

client_kem = oqs.KeyEncapsulation(KEM_ALGORITHM)


class KEMException(Exception):
    pass


def generate_shared_secret() -> bytes:
    '''
    Initiates and completes a key exchange in order to create a shared secret.
    '''
    
    # Get public key
    data = {'rpi_id': f'{CLIENT_ID}'}
    response = requests.post(f'{SERVER_URL}/kem/initiate', json=data)
    public_key_b64 = response.json().get('public_key_b64')
    if not public_key_b64:
        raise KEMException('Public key not found in response.')

    # Encapsulate a shared secret
    try:
        public_key = base64.b64decode(public_key_b64)
        ciphertext, shared_secret = client_kem.encap_secret(public_key)
    except Exception as e:
        raise KEMException('Invalid public key, could not encapsulate secret.')

    # Send encapsulated shared secret
    ciphertext_b64 = base64.b64encode(ciphertext).decode()
    data = {'rpi_id': f'{CLIENT_ID}', 'ciphertext_b64': ciphertext_b64}
    response = requests.post(f'{SERVER_URL}/kem/complete', json=data)
    if response.status_code != 201:
        raise KEMException(f'Unexpected status code: {response.status_code}.')
    
    return shared_secret

if __name__ == '__main__':
    # Example usage
    try:
        shared_secret = generate_shared_secret()
    except KEMException as e:
        print(f'KEM failed, could not generate secret: {e}')