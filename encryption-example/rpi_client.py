import requests
import oqs

CLIENT_ID = 42
KEM_ALGORITHM = 'Kyber512'
SERVER_URL = 'http://127.0.0.1:8000' # bug with urllib3, using http instead of https

client_kem = oqs.KeyEncapsulation(KEM_ALGORITHM)

# Get public key
data = {'rpi_id': f'{CLIENT_ID}'}
response = requests.post(f'{SERVER_URL}/kem/initiate', json=data)
public_key = response.json()['public_key']

# Encapsulate a shared secret
ciphertext, shared_secret = client_kem.encap_secret(public_key)

# Send encapsulated shared secret
data = {'rpi_id': CLIENT_ID, 'ciphertext': ciphertext}
response = requests.post(f'{SERVER_URL}/kem/complete', json=data)