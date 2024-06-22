import requests
import json
import argparse
from xml.etree.ElementTree import Element, SubElement, tostring

def get_proxmox_api_credentials(username, password, host):
    url = f"https://{host}:8006/api2/json/access/ticket"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'username': username,
        'password': password
    }

    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        response.raise_for_status()  # Raise exception for non-200 responses
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

def create_jenkins_credentials_xml(credentials_id, credentials_file):
    credentials_xml = Element('com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl')
    SubElement(credentials_xml, 'scope').text = 'GLOBAL'
    SubElement(credentials_xml, 'id').text = credentials_id
    SubElement(credentials_xml, 'description').text = 'Proxmox API credentials'

    with open(credentials_file, 'r') as f:
        credentials_json = json.load(f)

    SubElement(credentials_xml, 'username').text = credentials_json['username']
    SubElement(credentials_xml, 'password').text = credentials_json['password']

    return tostring(credentials_xml, encoding='unicode')

def add_jenkins_credentials(credentials_xml, jenkins_url, jenkins_user, api_token, jenkins_crumb):
    url = f"{jenkins_url}/credentials/store/system/domain/_/createCredentials"
    headers = {
        'Jenkins-Crumb': jenkins_crumb,
        'Content-Type': 'application/xml'
    }

    try:
        response = requests.post(url, headers=headers, auth=(jenkins_user, api_token), data=credentials_xml, verify=False)
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
    parser.add_argument('--jenkins-user', required=True, help="Jenkins username")
    parser.add_argument('--api-token', required=True, help="Jenkins API token")
    parser.add_argument('--jenkins-crumb', required=True, help="Jenkins crumb")

    args = parser.parse_args()

    ticket, csrf_token = get_proxmox_api_credentials(args.username, args.password, args.host)

    if ticket and csrf_token:
        save_credentials(ticket, csrf_token, args.credentials_file)
        credentials_xml = create_jenkins_credentials_xml(args.credentials_id, args.credentials_file)
        add_jenkins_credentials(credentials_xml, args.jenkins_url, args.jenkins_user, args.api_token, args.jenkins_crumb)
    else:
        print("Failed to generate credentials")
