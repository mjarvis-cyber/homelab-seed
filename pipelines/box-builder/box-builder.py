import argparse

def main():
    parser = argparse.ArgumentParser(description="Create Proxmox templates")
    parser.add_argument("--proxmox_ip", required=True, help="Proxmox IP address")
    parser.add_argument("--proxmox_node", required=True, help="Proxmox host to build the template on")
    parser.add_argument("--token_name", required=True, help="Proxmox API token name")
    parser.add_argument("--token_secret", required=True, help="Proxmox API token secret")
    parser.add_argument("--user", required=True, help="Proxmox SSH user")
    parser.add_argument("--password", required=True, help="Proxmox SSH password")

    args = parser.parse_args()

    proxmox_ip = args.proxmox_ip
    proxmox_node = args.proxmox_node
    token_name = args.token_name
    token_secret = args.token_secret
    proxmox_user = args.user
    proxmox_password = args.password

if __name__ == "__main__":
    main()