import requests
import json
import argparse
import os
import shutil

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

def delete_cluster_query(cluster_query, proxmox_ip, token_name, token_secret):
    api_url = f"https://{proxmox_ip}:8006/{cluster_query}"
    headers = {
        "Authorization": f"PVEAPIToken={token_name}={token_secret}"
    }

    response = requests.delete(api_url, headers=headers, verify=False)
    
    if response.status_code in (200, 204):
        return response.json() if response.content else "Deletion successful"
    else:
        response.raise_for_status()

def post_cluster_query(cluster_query, data, proxmox_ip, token_name, token_secret):
    api_url = f"https://{proxmox_ip}:8006/{cluster_query}"
    headers = {
        "Authorization": f"PVEAPIToken={token_name}={token_secret}"
    }

    if data:
        response = requests.post(api_url, headers=headers, data=data, verify=False)
    else:
        response = requests.post(api_url, headers=headers, verify=False)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def put_cluster_query(cluster_query, data, proxmox_ip, token_name, token_secret):
    api_url = f"https://{proxmox_ip}:8006/{cluster_query}"
    headers = {
        "Authorization": f"PVEAPIToken={token_name}={token_secret}"
    }

    response = requests.put(api_url, headers=headers, data=data, verify=False)
    
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

def get_qcow(image_url, qcow_dir, qcow_file, name):
    os.makedirs(qcow_dir, exist_ok=True)
    qcow_path = f"/tmp/{name}.img"

    response = requests.get(image_url, stream=True)
    response.raise_for_status()

    with open(qcow_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    shutil.move(qcow_path, qcow_file)

    print(f"Moving {qcow_path} to {qcow_dir}")
    os.system(f"qemu-img resize {qcow_file} 20G")

def create_vm(proxmox_ip, proxmox_node, token_name, token_secret, vmid, name):
    endpoint=f"api2/json/nodes/{proxmox_node}/qemu"
    data=f"vmid={vmid}&name={name}&full=1"
    post_cluster_query(endpoint, data, proxmox_ip, token_name, token_secret)

def vm_creation_pipeline(proxmox_ip, proxmox_node, token_name, token_secret, vmid, name, image_url, ssh_keys, qcow_dir, user, password, ip_to_use):
    qcow_file = f"{qcow_dir}/{name}.qcow2"
    print(f"Getting cloud image from {image_url} and placing in {qcow_file}")
    get_qcow(image_url, qcow_dir, qcow_file, name)
    print(f"Creating VM {name} with VMID: {vmid}")
    create_vm(proxmox_ip, proxmox_node, token_name, token_secret, vmid, name)

def runner(proxmox_ip, proxmox_node, token_name, token_secret, resource_pool_name, name, vmid_start, vmid_end, qcow_dir, ssh_keys, image_location, user, password, ip_to_use):
    vmid = pick_vmid(proxmox_ip, token_name, token_secret, vmid_start, vmid_end)
    print(f"Here is the vmid to use: {vmid}")
    vm_creation_pipeline(proxmox_ip, proxmox_node, token_name, token_secret, vmid, name, image_location, ssh_keys, qcow_dir, user, password, ip_to_use)

def main():
    parser = argparse.ArgumentParser(description="Create Proxmox templates")
    parser.add_argument("--proxmox_ip", required=True, help="Proxmox IP address")
    parser.add_argument("--proxmox_node", required=True, help="Proxmox host to build the template on")
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
            proxmox_node,
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
