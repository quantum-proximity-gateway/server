import requests
import oqs
import base64
from aesgcm_encryption import aesgcm_encrypt, aesgcm_decrypt
import uuid
import json
from pydantic import BaseModel

class KEMException(Exception):
    pass

class EncryptedResponse(BaseModel):
    nonce_b64: str
    ciphertext_b64: str

class EncryptionClient():
    def __init__(self, SERVER_URL):
        self.CLIENT_ID = str(uuid.uuid4())
        self.KEM_ALGORITHM = 'Kyber512'
        self.SERVER_URL = SERVER_URL  # Bug with urllib3, so using http instead of https
        self.shared_secret = self.generate_shared_secret()

    def generate_shared_secret(self) -> bytes:
        '''
        Initiates and completes a key exchange in order to create a shared secret.
        '''
        
        # Get public key
        data = {'client_id': str(self.CLIENT_ID)}
        response = requests.post(f'{self.SERVER_URL}/kem/initiate', json=data)
        public_key_b64 = response.json().get('public_key_b64')
        if not public_key_b64:
            raise KEMException('Public key not found in response.')

        # Encapsulate a shared secret
        with oqs.KeyEncapsulation(self.KEM_ALGORITHM) as client_kem:
            try:
                public_key = base64.b64decode(public_key_b64)
                ciphertext, shared_secret = client_kem.encap_secret(public_key)
            except Exception as e:
                raise KEMException('Invalid public key, could not encapsulate secret.')

        # Send encapsulated shared secret
        ciphertext_b64 = base64.b64encode(ciphertext).decode()
        data = {'client_id': str(self.CLIENT_ID), 'ciphertext_b64': ciphertext_b64}
        response = requests.post(f'{self.SERVER_URL}/kem/complete', json=data)
        if response.status_code != 201:
            raise KEMException(f'Unexpected status code: {response.status_code}.')
        
        return shared_secret

    def encrypt_request(self, plaintext: str) -> dict:
        plaintext_str = json.dumps(plaintext)

        nonce_b64, ciphertext_b64 = aesgcm_encrypt(plaintext_str, self.shared_secret)

        data = {
            'client_id': str(self.CLIENT_ID),
            'nonce_b64': nonce_b64,
            'ciphertext_b64': ciphertext_b64
        }

        return data

    def decrypt_request(self, data: dict) -> dict: # pass in response.json()
        try:
            validated_data = EncryptedResponse(**data)
        except ValueError as e:
            raise RuntimeError(f'Invalid response data: {e}')
        
        try:
            plaintext = aesgcm_decrypt(validated_data.nonce_b64, validated_data.ciphertext_b64, self.shared_secret)
            return json.loads(plaintext)
        except Exception as e:
            raise RuntimeError(f'Error: {e}\nFailed to decrypt response data.')