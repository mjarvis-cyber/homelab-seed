import os
import requests
import argparse

def download_iso(iso_url, output_path):
    response = requests.get(iso_url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Downloaded ISO to {output_path}")
    else:
        response.raise_for_status()

def upload_iso_to_proxmox(proxmox_ip, node, storage, iso_path, token_name, token_secret):
    api_url = f"https://{proxmox_ip}:8006/api2/json/nodes/{node}/storage/{storage}/upload"
    headers = {
        "Authorization": f"PVEAPIToken={token_name}={token_secret}"
    }
    
    with open(iso_path, 'rb') as file:
        files = {
            'content': (None, 'iso'),
            'filename': (os.path.basename(iso_path), file)
        }
        response = requests.post(api_url, headers=headers, files=files, verify=False, stream=True)
        
        if response.status_code == 200:
            print(f"Uploaded ISO {iso_path} to {node}/{storage}")
        else:
            response.raise_for_status()

def main():
    parser = argparse.ArgumentParser(description="Download and upload an ISO to Proxmox")
    parser.add_argument("--proxmox_ip", required=True, help="Proxmox IP address")
    parser.add_argument("--proxmox_node", required=True, help="Proxmox node")
    parser.add_argument("--iso_url", required=True, help="URL to get the iso from")
    parser.add_argument("--token_name", required=True, help="Proxmox API token name")
    parser.add_argument("--token_secret", required=True, help="Proxmox API token secret")
    
    args = parser.parse_args()

    proxmox_ip = args.proxmox_ip
    proxmox_node = args.proxmox_node
    token_name = args.token_name
    token_secret = args.token_secret
    storage = "local"
    iso_url = args.iso_url

    # Extract the filename from the URL and set the path in /tmp
    iso_filename = os.path.basename(iso_url)
    iso_path = f"/tmp/{iso_filename}"
    
    print(f"Running download_iso({iso_url})")
    download_iso(iso_url, iso_path)
    
    print(f"Running upload_iso_to_proxmox {proxmox_ip}, {proxmox_node}, {storage}, {iso_path}, {token_name}, {token_secret}")
    upload_iso_to_proxmox(proxmox_ip, proxmox_node, storage, iso_path, token_name, token_secret)
    
    os.remove(iso_path)
    print(f"Removed ISO from {iso_path}")

if __name__ == "__main__":
    main()
