import time
import statistics
import base64
import json
import oqs
import numpy as np
from encryption_helper import EncryptionHelper
from aesgcm_encryption import aesgcm_encrypt, aesgcm_decrypt

def benchmark_function(func, iterations=1000, *args, **kwargs):
    results = []
    for _ in range(iterations):
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        results.append(end_time - start_time)
    
    return {
        "min": min(results),
        "max": max(results),
        "mean": statistics.mean(results),
        "median": statistics.median(results),
        "p95": sorted(results)[int(iterations * 0.95)],
        "p99": sorted(results)[int(iterations * 0.99)],
        "stddev": statistics.stdev(results) if len(results) > 1 else 0
    }

def benchmark_kem_operation():
    # Test ML-KEM-512 operations
    print("Benchmarking ML-KEM-512 operations...")
    
    def complete_kem_cycle():
        # Generate key pair
        with oqs.KeyEncapsulation('ML-KEM-512') as server_kem:
            public_key = server_kem.generate_keypair()
            
            # Client encapsulation
            with oqs.KeyEncapsulation('ML-KEM-512') as client_kem:
                ciphertext, shared_secret_client = client_kem.encap_secret(public_key)
            
            # Server decapsulation
            shared_secret_server = server_kem.decap_secret(ciphertext)
            
            # Verify shared secrets match
            assert shared_secret_client == shared_secret_server
    
    results = benchmark_function(complete_kem_cycle, iterations=500)
    print("Complete KEM cycle (ms):", {k: v*1000 for k, v in results.items()})

def benchmark_encryption_helper():
    print("\nBenchmarking EncryptionHelper operations...")
    helper = EncryptionHelper()
    client_id = "test_client"
    
    # Set up a shared secret for testing
    with oqs.KeyEncapsulation('ML-KEM-512') as kem:
        public_key = kem.generate_keypair()
        with oqs.KeyEncapsulation('ML-KEM-512') as client_kem:
            ciphertext, shared_secret = client_kem.encap_secret(public_key)
        helper.shared_secrets[client_id] = shared_secret
    
    test_data = {"username": "testuser", "password": "testpassword", "data": "x" * 1000}
    
    # Test encryption
    def encrypt_message():
        return helper.encrypt_msg(test_data, client_id)
    
    results_encrypt = benchmark_function(encrypt_message, iterations=1000)
    print("Encrypt message (ms):", {k: v*1000 for k, v in results_encrypt.items()})
    
    # Test decryption
    encrypted = helper.encrypt_msg(test_data, client_id)
    request = type('EncryptedMessageRequest', (), {
        'client_id': client_id,
        'nonce_b64': encrypted['nonce_b64'],
        'ciphertext_b64': encrypted['ciphertext_b64']
    })
    
    def decrypt_message():
        return helper.decrypt_msg(request)
    
    results_decrypt = benchmark_function(decrypt_message, iterations=1000)
    print("Decrypt message (ms):", {k: v*1000 for k, v in results_decrypt.items()})

if __name__ == "__main__":
    benchmark_kem_operation()
    benchmark_encryption_helper()