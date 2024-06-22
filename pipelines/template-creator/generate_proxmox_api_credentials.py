import requests
import json
import argparse

def get_proxmox_api_credentials(username, password, host):
    url = f"https://{host}:8006/api2/json/access/ticket"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'username': username,
        'password': password
    }

    response = requests.post(url, headers=headers, data=data, verify=False)

    if response.status_code == 200:
        result = response.json()
        ticket = result['data']['ticket']
        csrf_token = result['data']['CSRFPreventionToken']
        return ticket, csrf_token
    else:
        print(f"Failed to login: {response.status_code}")
        print(response.text)
        return None, None

def save_credentials(ticket, csrf_token, credentials_file):
    credentials = {
        'ticket': ticket,
        'csrf_token': csrf_token
    }
    with open(credentials_file, 'w') as f:
        json.dump(credentials, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Proxmox API credentials")
    parser.add_argument('--username', required=True, help="Proxmox username")
    parser.add_argument('--password', required=True, help="Proxmox password")
    parser.add_argument('--host', required=True, help="Proxmox host")
    parser.add_argument('--credentials-file', default='proxmox_credentials.json', help="File to save the credentials")

    args = parser.parse_args()

    ticket, csrf_token = get_proxmox_api_credentials(args.username, args.password, args.host)

    if ticket and csrf_token:
        save_credentials(ticket, csrf_token, args.credentials_file)
        print("Credentials saved successfully")
    else:
        print("Failed to generate credentials")
