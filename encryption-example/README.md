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

### 3. Run Litestar server

```bash
# Start Litestar server
litestar run
```

### 4. Run example client code

```bash
# Run example Raspberry Pi client code
python rpi_client.py
```

If the setup was successful, you should see a message outputted to the server terminal saying "Server received: Hello, Litestar!", and another message on the client side saying "Client received: Hello, Raspberry Pi #42!".