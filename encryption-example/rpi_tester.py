from encryption_client import EncryptionClient
import requests
# A script useful to test our server

if __name__ == "__main__":
    server_url = "http://127.0.0.1:8000"
    encryption_client = EncryptionClient(server_url)
    try:
        response = requests.get(f"{server_url}/devices/all-mac-addresses", params={'client_id': encryption_client.CLIENT_ID})
        response.raise_for_status()
        response_json = response.json()
        data = encryption_client.decrypt_request(response_json)

        print([mac.strip() for mac in data['mac_addresses']])

    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching MAC addresses: {e}")

