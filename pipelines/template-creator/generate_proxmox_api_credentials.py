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

    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        response.raise_for_status()
        result = response.json()
        ticket = result['data']['ticket']
        csrf_token = result['data']['CSRFPreventionToken']
        return ticket, csrf_token
    except requests.exceptions.RequestException as e:
        print(f"Failed to get credentials: {e}")
        return None, None

def save_credentials(ticket, csrf_token, credentials_file):
    credentials = {
        'ticket': ticket,
        'csrf_token': csrf_token
    }
    with open(credentials_file, 'w') as f:
        json.dump(credentials, f)

def add_jenkins_credentials(credentials_id, credentials_file, jenkins_url, jenkins_username, jenkins_password):
    url = f"{jenkins_url}/credentials/store/system/domain/_/createCredentials"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    with open(credentials_file, 'r') as f:
        credentials_json = json.load(f)

    data = {
        'json': json.dumps({
            '': '0',
            'credentials': {
                'scope': 'GLOBAL',
                'id': credentials_id,
                'secret': json.dumps(credentials_json),
                'description': 'Proxmox API credentials',
                'stapler-class': 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl'
            }
        })
    }

    try:
        response = requests.post(url, headers=headers, auth=(jenkins_username, jenkins_password), data=data, verify=False)
        response.raise_for_status()  # Raise exception for non-200 responses
        print("Credentials added successfully to Jenkins")
    except requests.exceptions.RequestException as e:
        print(f"Failed to add credentials to Jenkins: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Proxmox API credentials and add to Jenkins")
    parser.add_argument('--username', required=True, help="Proxmox username")
    parser.add_argument('--password', required=True, help="Proxmox password")
    parser.add_argument('--host', required=True, help="Proxmox host")
    parser.add_argument('--credentials-id', required=True, help="Jenkins credentials ID")
    parser.add_argument('--credentials-file', default='proxmox_credentials.json', help="File to save the credentials")
    parser.add_argument('--jenkins-url', required=True, help="Jenkins base URL")
    parser.add_argument('--jenkins-username', required=True, help="Jenkins username")
    parser.add_argument('--jenkins-password', required=True, help="Jenkins password")

    args = parser.parse_args()

    ticket, csrf_token = get_proxmox_api_credentials(args.username, args.password, args.host)

    if ticket and csrf_token:
        save_credentials(ticket, csrf_token, args.credentials_file)
        add_jenkins_credentials(args.credentials_id, args.credentials_file, args.jenkins_url, args.jenkins_username, args.jenkins_password)
    else:
        print("Failed to generate credentials")
