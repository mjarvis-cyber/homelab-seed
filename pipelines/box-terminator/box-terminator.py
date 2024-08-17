import argparse
import requests
import time

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

def post_cluster_query(cluster_query, data, proxmox_ip, token_name, token_secret):
    api_url = f"https://{proxmox_ip}:8006/{cluster_query}"
    headers = {
        "Authorization": f"PVEAPIToken={token_name}={token_secret}"
    }

    response = requests.post(api_url, headers=headers, data=data, verify=False)
    
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
        return "Deletion successful"
    else:
        response.raise_for_status()

def is_vmid_locked(proxmox_ip, proxmox_node, token_name, token_secret, vm_id):
    cluster_query = f"api2/json/nodes/{proxmox_node}/qemu/{vm_id}/status/current"
    vm_status = get_cluster_query_output(cluster_query, proxmox_ip, token_name, token_secret)
    return 'lock' in vm_status['data']

def wait_for_vmid_unlock(proxmox_ip, proxmox_node, token_name, token_secret, vm_id, check_interval=10):
    while is_vmid_locked(proxmox_ip, proxmox_node, token_name, token_secret, vm_id):
        print(f"VMID {vm_id} is locked. Waiting for {check_interval} seconds...")
        time.sleep(check_interval)
    
    print(f"VMID {vm_id} is no longer locked.")

def find_vm_node(proxmox_ip, vmid, token_name, token_secret):
    vms = get_cluster_query_output("api2/json/cluster/resources", proxmox_ip, token_name, token_secret)["data"]
    for vm in vms:
        if vm["type"] == "qemu" and vm["vmid"] == vmid:
            return vm["node"]
    raise ValueError(f"VM with ID {vmid} not found.")

def stop_vm(proxmox_ip, node, vmid, token_name, token_secret):
    stop_endpoint = f"api2/json/nodes/{node}/qemu/{vmid}/status/stop"
    print(f"Stopping VM {vmid} on node {node}...")
    post_cluster_query(stop_endpoint, None, proxmox_ip, token_name, token_secret)
    print(f"VM {vmid} stopped successfully.")

def delete_vm(proxmox_ip, node, vmid, token_name, token_secret):
    delete_endpoint = f"api2/json/nodes/{node}/qemu/{vmid}?destroy-unreferenced-disks=1&purge=1"
    print(f"Deleting VM {vmid} on node {node}...")
    delete_cluster_query(delete_endpoint, proxmox_ip, token_name, token_secret)
    print(f"VM {vmid} deleted successfully.")

def main():
    parser = argparse.ArgumentParser(description="Delete a Proxmox VM")
    parser.add_argument("--proxmox_ip", required=True, help="Proxmox IP address")
    parser.add_argument("--vmid", required=True, type=int, help="VM ID to delete")
    parser.add_argument("--token_name", required=True, help="Proxmox API token name")
    parser.add_argument("--token_secret", required=True, help="Proxmox API token secret")
    
    args = parser.parse_args()

    proxmox_ip = args.proxmox_ip
    vmid = args.vmid
    token_name = args.token_name
    token_secret = args.token_secret

    node = find_vm_node(proxmox_ip, vmid, token_name, token_secret)
    print(f"VM {vmid} is running on node {node}.")

    stop_vm(proxmox_ip, node, vmid, token_name, token_secret)
    wait_for_vmid_unlock(proxmox_ip, node, token_name, token_secret, vmid)
    print("Waiting 30 seconds for the machine to actually shut down")
    time.sleep(30)
    
    delete_vm(proxmox_ip, node, vmid, token_name, token_secret)

if __name__ == "__main__":
    main()
