# Post-quantum cryptography example

This example demonstrates a post-quantum secure key exchange using the Kyber512 Key Encapsulation Mechanism (KEM) to establish a shared secret between a client and server, which is then used as a symmetric key for encryption of messages via AES-GCM.

## Example setup

Before you begin, ensure you are within the `encryption-example/` directory.

### 1. Create a Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Install liboqs-python package
cd liboqs-python/
pip install .
```

If liboqs is not detected at runtime by liboqs-python, it will be downloaded, configured and installed automatically.