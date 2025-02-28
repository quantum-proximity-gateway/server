import requests
import oqs
import base64

CLIENT_ID = 42
KEM_ALGORITHM = 'Kyber512'
SERVER_URL = 'http://127.0.0.1:8000' # bug with urllib3, using http instead of https

client_kem = oqs.KeyEncapsulation(KEM_ALGORITHM)


def generate_shared_secret() -> bytes:
    # Get public key
    data = {'rpi_id': f'{CLIENT_ID}'}
    response = requests.post(f'{SERVER_URL}/kem/initiate', json=data)
    public_key_b64 = response.json().get('public_key')
    if not public_key_b64:
        raise
    public_key = base64.b64decode(public_key_b64)
    # print(f'Public key: {public_key}')

    # Encapsulate a shared secret
    ciphertext, shared_secret = client_kem.encap_secret(public_key)
    print(f'Shared secret: {shared_secret}')

    # Send encapsulated shared secret
    data = {'rpi_id': f'{CLIENT_ID}', 'ciphertext': base64.b64encode(ciphertext).decode()}
    response = requests.post(f'{SERVER_URL}/kem/complete', json=data)
    if response.status_code != 201:
        raise
    
    return shared_secret

generate_shared_secret()