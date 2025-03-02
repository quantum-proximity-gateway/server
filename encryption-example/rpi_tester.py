from encryption_client import EncryptionClient
import requests
# A script useful to test our server

if __name__ == "__main__":
    server_url = "http://127.0.0.1:8000"
    encryption_client = EncryptionClient(server_url)
    macs = []

    # Testing get-all-usernames
    try:
        response = requests.get(f"{server_url}/devices/all-mac-addresses", params={'client_id': encryption_client.CLIENT_ID})
        response.raise_for_status()
        response_json = response.json()
        data = encryption_client.decrypt_request(response_json)

        macs = [mac.strip() for mac in data['mac_addresses']]
        print(macs)
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching MAC addresses: {e}")

    # Testing get-username
    try:
        response = requests.get(f"{server_url}/devices/{macs[0]}/username", params={'client_id': encryption_client.CLIENT_ID})
        response.raise_for_status()
        data = encryption_client.decrypt_request(response.json())

        print(data.get("username", "invalid"))

    except requests.exceptions.RequestException as e:
        print(f"Error fetching username for MAC address {macs[0]}: {e}")

    # Testing get-credentials
    try:
        response = requests.get(f"{server_url}/devices/{macs[0]}/credentials", params={'client_id': encryption_client.CLIENT_ID})
        response.raise_for_status()
        data = encryption_client.decrypt_request(response.json())

        print(data.get("username", "invalid"), data.get("password", "invalid"))

    except requests.exceptions.RequestException as e:
        print(f"Error fetching username for MAC address {macs[0]}: {e}")

