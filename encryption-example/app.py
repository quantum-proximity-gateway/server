from litestar import Litestar, post
from litestar.exceptions import HTTPException
from pydantic import BaseModel
import oqs
import base64
from aesgcm_encryption import aesgcm_encrypt, aesgcm_decrypt

KEM_ALGORITHM = 'Kyber512'

kem_sessions = {}
shared_secrets = {}


class KEMInitiateRequest(BaseModel):
    client_id: str


class KEMCompleteRequest(BaseModel):
    client_id: str
    ciphertext_b64: str


class EncryptedMessageRequest(BaseModel):
    client_id: str
    nonce_b64: str
    ciphertext_b64: str


@post('/kem/initiate')
async def kem_initiate(data: KEMInitiateRequest) -> dict:
    '''
    Initiate key exchange session. The server generates a KEM key pair and returns the public key.
    '''

    server_kem = oqs.KeyEncapsulation(KEM_ALGORITHM)
    kem_sessions[data.client_id] = server_kem
    public_key = server_kem.generate_keypair()
    public_key_b64 = base64.b64encode(public_key).decode()
    return {'public_key_b64': public_key_b64}

@post('/kem/complete')
async def kem_complete(data: KEMCompleteRequest) -> dict:
    '''
    Complete the key exchange. The client sends back the encapsulated shared secret that they have generated.
    '''

    server_kem = kem_sessions.pop(data.client_id, None)
    if not server_kem:
        raise HTTPException(status_code=401, detail='Client not recognised, please initiate a new key exchange session.')
    
    try:
        ciphertext = base64.b64decode(data.ciphertext_b64)
        shared_secret = server_kem.decap_secret(ciphertext)
    except Exception as e:
        raise HTTPException(status_code=400, detail='Failed to decrypt data.')
    shared_secrets[data.client_id] = shared_secret
    return {'status': 'success'}

@post('/example-endpoint')
async def example_endpoint(data: EncryptedMessageRequest) -> dict:
    '''
    Example API endpoint which demonstrates decrypting incoming request data, and encrypting outgoing response data.
    '''

    shared_secret = shared_secrets.get(data.client_id, None)
    if not shared_secret:
        raise HTTPException(status_code=404, detail='Shared secret not found.')
    
    try:
        plaintext = aesgcm_decrypt(data.nonce_b64, data.ciphertext_b64, shared_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail='Failed to decrypt data.')
    print(f'Server received: {plaintext}')

    response_text = f'Hello, Raspberry Pi #{data.client_id}!'
    nonce_b64, ciphertext_b64 = aesgcm_encrypt(response_text, shared_secret)
    return {'nonce_b64': nonce_b64, 'ciphertext_b64': ciphertext_b64}


app = Litestar(
    route_handlers=[
        kem_initiate,
        kem_complete,
        example_endpoint,
    ],
    debug=True
)