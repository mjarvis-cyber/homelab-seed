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
    time.sleep(5) # time for proxmox to do stuff
    vmid_start = int(vmid_start)
    vmid_end = int(vmid_end)
    vm_metadata = get_vm_metadata(proxmox_ip, token_name, token_secret)
    used_vmids = vm_metadata.keys()
    for vmid in range(vmid_start, vmid_end + 1):
        if vmid not in used_vmids:
            return vmid
    raise ValueError("No available VMID found in the specified range")

def find_template(proxmox_ip, proxmox_node, token_name, token_secret, template_name):
    cluster_query = f"api2/json/nodes/{proxmox_node}/qemu"
    vms = get_cluster_query_output(cluster_query, proxmox_ip, token_name, token_secret)
    
    # Iterate through the VMs to find the one that matches the template name and is marked as a template
    for vm in vms['data']:
        if vm['name'] == template_name and vm.get('template', 0) == 1:
            return vm['vmid']
    
    return None

#def clone_template(proxmox_ip, token_name, token_secret, template_vmid, vm_id, pool):
    

def create_box(proxmox_ip, proxmox_node, token_name, token_secret, low_vmid, high_vmid, template_name):
    print(f"Picking a VMID between {low_vmid} and {high_vmid}")
    vmid_to_use=pick_vmid(proxmox_ip, token_name, token_secret, low_vmid, high_vmid)
    print(f"Picked VMID {vmid_to_use} on {proxmox_node}")
    print(f"Finding the VMID of the {template_name} template on {proxmox_node}")
    template_vmid=find_template(proxmox_ip, proxmox_node, token_name, token_secret, template_name)
    if template_vmid is None:
        print(f"Critical failure, could not find {template_name} on {proxmox_node}, aborting")
        SystemExit
    else:
        print(f"Proceeding to build VM {vmid_to_use} on {proxmox_node}, based on {template_vmid}")

def main():
    parser = argparse.ArgumentParser(description="Create Proxmox templates")
    parser.add_argument("--proxmox_ip", required=True, help="Proxmox IP address")
    parser.add_argument("--proxmox_node", required=True, help="Proxmox host to build the box on")
    parser.add_argument("--proxmox_pool", required=True, help="Proxmox resource pool to build the box in")
    parser.add_argument("--token_name", required=True, help="Proxmox API token name")
    parser.add_argument("--token_secret", required=True, help="Proxmox API token secret")
    parser.add_argument("--low_vmid", required=True, help="The lowest VMID in the pool to use")
    parser.add_argument("--high_vmid", required=True, help="The highest VMID in the pool to use")
    parser.add_argument("--template_name", required=True, help="The name of the template to use")

    args = parser.parse_args()
    proxmox_ip      = args.proxmox_ip
    proxmox_node    = args.proxmox_node
    token_name      = args.token_name
    token_secret    = args.token_secret
    low_vmid        = args.low_vmid
    high_vmid       = args.high_vmid
    template_name   = args.template_name
    #try:
    create_box(proxmox_ip, proxmox_node, token_name, token_secret, low_vmid, high_vmid, template_name)
    #except Exception as E:
    #    print(f"Failed to provision resource, attempting to delete it: {E}")

if __name__ == "__main__":
    main()