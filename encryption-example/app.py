from litestar import Litestar, get, post
from litestar.exceptions import HTTPException
from pydantic import BaseModel
import oqs
import base64
from aesgcm_encryption import aesgcm_encrypt, aesgcm_decrypt

KEM_ALGORITHM = 'Kyber512'

kem_sessions = {}
shared_secrets = {}


class KEMInitiateRequest(BaseModel):
    rpi_id: str


class KEMCompleteRequest(BaseModel):
    rpi_id: str
    ciphertext_b64: str


class EncryptedMessageRequest(BaseModel):
    rpi_id: str
    nonce_b64: str
    ciphertext_b64: str


@post('/kem/initiate')
def kem_initiate(data: KEMInitiateRequest) -> dict:
    '''
    Initiate key exchange session. The server generates a KEM key pair and returns the public key.
    '''

    server_kem = oqs.KeyEncapsulation(KEM_ALGORITHM)
    kem_sessions[data.rpi_id] = server_kem
    public_key = server_kem.generate_keypair()
    public_key_b64 = base64.b64encode(public_key).decode()
    return {'public_key_b64': public_key_b64}

@post('/kem/complete')
def kem_complete(data: KEMCompleteRequest) -> dict:
    '''
    Complete the key exchange. The client sends back the encapsulated shared secret that they have generated.
    '''

    server_kem = kem_sessions.pop(data.rpi_id, None)
    if not server_kem:
        raise HTTPException(status_code=401, detail='Client not recognised, please initiate a new key exchange session.')
    
    ciphertext = base64.b64decode(data.ciphertext_b64)
    shared_secret = server_kem.decap_secret(ciphertext)
    shared_secrets[data.rpi_id] = shared_secret
    return {'status': 'success'}

@get('/example-endpoint')
def example_endpoint(data: EncryptedMessageRequest) -> dict:

    return


app = Litestar(
    route_handlers=[
        kem_initiate,
        kem_complete,
        example_endpoint,
    ],
    debug=True
)