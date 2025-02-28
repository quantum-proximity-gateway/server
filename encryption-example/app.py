from litestar import Litestar, get, post
from litestar.exceptions import HTTPException
from pydantic import BaseModel
import oqs

KEM_ALGORITHM = 'Kyber512'

kem_sessions = {}
shared_secrets = {}


class KEMInitiateRequest(BaseModel):
    rpi_id: str


class KEMCompleteRequest(BaseModel):
    rpi_id: str
    ciphertext: str


@post('/kem/initiate')
def kem_initiate(data: KEMInitiateRequest) -> dict:
    '''
    Initiate key exchange session. The server generates a KEM key pair and returns the public key.
    '''

    server_kem = oqs.KeyEncapsulation(KEM_ALGORITHM)
    kem_sessions[data.rpi_id] = server_kem
    public_key = server_kem.generate_keypair()
    return {'public_key': public_key}

@post('/kem/complete')
def kem_complete(data: KEMCompleteRequest) -> dict:
    '''
    Complete the key exchange. The client sends back the encapsulated shared secret that they have generated.
    '''

    server_kem = kem_sessions.pop(data.rpi_id, None)
    if not server_kem:
        raise HTTPException(status_code=401, detail='Client not recognised, please initiate a key exchange session')
    
    shared_secret = server_kem.decap_secret(data.ciphertext)
    shared_secrets[data.rpi_id] = shared_secret
    return {'status': 'success'}

app = Litestar(
    route_handlers=[
        kem_initiate,
        kem_complete,
    ],
    debug=True
)