from pydantic import BaseModel
import oqs
import base64
from aesgcm_encryption import aesgcm_encrypt, aesgcm_decrypt


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
