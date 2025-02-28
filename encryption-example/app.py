from litestar import Litestar, get, post
from pydantic import BaseModel
import oqs

KEM_ALGORITHM = 'Kyber512'


class KEMInitiateRequest(BaseModel):
    rpi_id: str


@post('/kem/initiate')
def kem_initiate(data: KEMInitiateRequest) -> dict:
    '''
    Initiate key exchange session. The server generates a KEM key pair and returns the public key.
    '''

    


app = Litestar(
    route_handlers=[
        kem_initiate,
    ],
    debug=True
)