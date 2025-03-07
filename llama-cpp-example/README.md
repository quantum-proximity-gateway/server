# Llama-cpp-python example

This example demonstrates example usage of the llama-cpp-python library.

## Example setup

Before you begin, ensure you are within the `llama-cpp-example/` directory.

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
```

### 3. Create `models/` directory and download IBM Granite model

```bash
# Create models/ directory
mkdir models
cd models

# Download the granite-3.2-8b-instruct-Q6_K_L model
wget https://huggingface.co/bartowski/ibm-granite_granite-3.2-8b-instruct-GGUF/resolve/main/ibm-granite_granite-3.2-8b-instruct-Q6_K_L.gguf
```

### 4. Run example code

```bash
# Run example code
python main.py
```

If the setup was successful, you should see the response by the IBM Granite model outputted to the terminal.