from pydantic import BaseModel
import oqs
import base64
from aesgcm_encryption import aesgcm_encrypt, aesgcm_decrypt
import json
from litestar import Litestar, post
from litestar.exceptions import HTTPException

class EncryptionHelper():
    def __init__(self):
        self.KEM_ALGORITHM = 'Kyber512'
        self.kem_sessions = {}
        self.shared_secrets = {}
    
    class KEMInitiateRequest(BaseModel):
        client_id: str


    class KEMCompleteRequest(BaseModel):
        client_id: str
        ciphertext_b64: str


    class EncryptedMessageRequest(BaseModel):
        client_id: str
        nonce_b64: str
        ciphertext_b64: str

    def decrypt_msg(self, data: dict):
        try:
            validated_data = self.EncryptedMessageRequest(**data)
            shared_secret = self.shared_secrets.get(validated_data.client_id)
            if not shared_secret:
                raise ValueError("Shared secret not found for client_id")

            plaintext = aesgcm_decrypt(validated_data.nonce_b64, validated_data.ciphertext_b64, shared_secret)
            return json.loads(plaintext)
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt message: {e}")

    def encrypt_msg(self, data: dict, client_id):
        shared_secret = self.shared_secrets.get(client_id)
        if not shared_secret:
            raise ValueError("Shared secret not found for client_id")
        nonce_b64, ciphertext_b64 = aesgcm_encrypt(json.dumps(data), shared_secret)
        return {'nonce_b64': nonce_b64, 'ciphertext_b64': ciphertext_b64}
    
    @post('/kem/initiate')
    async def kem_initiate(self, data: KEMInitiateRequest) -> dict:
        '''
        Initiate key exchange session. The server generates a KEM key pair and returns the public key.
        '''

        server_kem = oqs.KeyEncapsulation(self.KEM_ALGORITHM)
        self.kem_sessions[data.client_id] = server_kem
        public_key = server_kem.generate_keypair()
        public_key_b64 = base64.b64encode(public_key).decode()
        return {'public_key_b64': public_key_b64}

    @post('/kem/complete')
    async def kem_complete(self, data: KEMCompleteRequest) -> dict:
        '''
        Complete the key exchange. The client sends back the encapsulated shared secret that they have generated.
        '''

        server_kem = self.kem_sessions.pop(data.client_id, None)
        if not server_kem:
            raise HTTPException(status_code=401, detail='Client not recognised, please initiate a new key exchange session.')
        
        try:
            ciphertext = base64.b64decode(data.ciphertext_b64)
            shared_secret = server_kem.decap_secret(ciphertext)
        except Exception as e:
            raise HTTPException(status_code=400, detail='Failed to decrypt data.')
        finally:
            server_kem.free()
        
        self.shared_secrets[data.client_id] = shared_secret
        return {'status': 'success'}