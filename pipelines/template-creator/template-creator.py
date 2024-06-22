import requests
import json
import argparse

def get_cluster_query_output(cluster_query, proxmox_ip, token_name, token_secret):
    api_url = f"https://{proxmox_ip}:8006/{cluster_query}"
    headers = {
        "Authorization": f"PVEAPIToken={token_name}={token_secret}"
    }
    
    response = requests.get(api_url, headers=headers, verify=False)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_vm_metadata(proxmox_ip, token_name, token_secret):
    vm_data = {}
    vmids = get_cluster_query_output("api2/json/cluster/resources", proxmox_ip, token_name, token_secret)["data"]
    for vm in vmids:
        if vm["type"] == "qemu":
            vm_data[vm["vmid"]] = {}
            vm_data[vm["vmid"]]["proxmox_node"] = vm["node"]
            vm_data[vm["vmid"]]["status"] = vm["status"]
    return vm_data

def pick_vmid(proxmox_ip, token_name, token_secret, vmid_start, vmid_end):
    vm_metadata = get_vm_metadata(proxmox_ip, token_name, token_secret)
    used_vmids = vm_metadata.keys()
    for vmid in range(vmid_start, vmid_end + 1):
        if vmid not in used_vmids:
            return vmid
    raise ValueError("No available VMID found in the specified range")

def runner(proxmox_ip, token_name, token_secret, resource_pool_name, name, vmid_start, vmid_end, qcow_dir, ssh_keys, image_location, user, password, ip_to_use):
    vmid = pick_vmid(proxmox_ip, token_name, token_secret, vmid_start, vmid_end)
    print(f"Here is the vmid to use: {vmid}")

def main():
    parser = argparse.ArgumentParser(description="Create Proxmox templates")
    parser.add_argument("--proxmox_ip", required=True, help="Proxmox IP address")
    parser.add_argument("--token_name", required=True, help="Proxmox API token name")
    parser.add_argument("--token_secret", required=True, help="Proxmox API token secret")

    args = parser.parse_args()

    proxmox_ip = args.proxmox_ip
    token_name = args.token_name
    token_secret = args.token_secret

    with open("configs.json", "r") as file:
        config = json.load(file)

    for template_name, template in config['templates'].items():
        ssh_keys_file = f"{template_name}-keys.pub"
        with open(ssh_keys_file, 'w') as file:
            file.write("\n".join(template['ssh_keys']))

        runner(
            proxmox_ip,
            token_name,
            token_secret,
            config['resource_pool'],
            template_name,
            config['template_start_id'],
            config['template_end_id'],
            config['qcow_dir'],
            ssh_keys_file,
            template['img_url'],
            template['user'],
            template['password'],
            config['temporary_ip']
        )

if __name__ == "__main__":
    main()
