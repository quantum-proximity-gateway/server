from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64


def aesgcm_encrypt(plaintext: str, shared_secret: bytes) -> tuple[str, str]:
    '''
    Returns a tuple containing the nonce and ciphertext, each of which are a base64 encoded string.
    '''

    # Generate a random 12-byte nonce (number once or 'nonce' is a random number that should only be used once)
    nonce = os.urandom(12)

    # Encrypt the plaintext
    aesgcm = AESGCM(shared_secret)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    nonce_b64 = base64.b64encode(nonce).decode()
    ciphertext_b64 = base64.b64encode(ciphertext).decode()
    return nonce_b64, ciphertext_b64

def aesgcm_decrypt(nonce_b64: str, ciphertext_b64: str, shared_secret: bytes) -> str:
    '''
    Returns the plaintext as a string.
    '''

    # Convert from base64 encoded string to bytes
    nonce = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)

    # Decrypt the ciphertext
    aesgcm = AESGCM(shared_secret)
    plaintext = aesgcm.decrypt(nonce, ciphertext)

    return plaintext.decode() # convert from bytes to str