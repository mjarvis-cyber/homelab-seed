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

def clone_template(proxmox_ip, proxmox_node, token_name, token_secret, template_vmid, vm_id, vm_name, pool):
    cluster_query = f"api2/json/nodes/{proxmox_node}/qemu/{template_vmid}/clone"
    data = {
        "newid": vm_id,
        "name": vm_name,
        "pool": pool
    }
    response = post_cluster_query(cluster_query, data, proxmox_ip, token_name, token_secret)
    
    return response

def check_pool(proxmox_ip, token_name, token_secret, pool_name):
    # check if pool exists already
    endpoint = "api2/json/pools"
    response = get_cluster_query_output(endpoint, proxmox_ip, token_name, token_secret)
    
    existing_pools = response.get('data', [])
    
    if not existing_pools:
        print(f"No pools found.")
        return False
    
    pool_ids = [pool.get('poolid', '') for pool in existing_pools]
    
    if pool_name in pool_ids:
        print(f"Pool '{pool_name}' already exists.")
        return True
    else:
        print(f"Pool {pool_name} not found")
        return False

def create_pool(proxmox_ip, token_name, token_secret, pool_name):
    endpoint = "api2/json/pools"
    data={}
    data["poolid"]=pool_name
    post_cluster_query(cluster_query=endpoint, data=data, proxmox_ip=proxmox_ip, token_name=token_name, token_secret=token_secret)

def ensure_resource_pool(proxmox_ip, token_name, token_secret, pool_name):
    exists = check_pool(proxmox_ip, token_name, token_secret, pool_name)
    if not exists:
        create_pool(proxmox_ip, token_name, token_secret, pool_name)    

def configure_vm(proxmox_ip, proxmox_node, token_name, token_secret, vmid, cores, memory, network):
    endpoint=f"api2/json/nodes/{proxmox_node}/qemu{vmid}/config"
    data={}
    data["cores"]=cores
    data["memory"]={memory}
    data["net0"]=f"virtio,bridge={network}"
    post_cluster_query(endpoint, data, proxmox_ip, token_name, token_secret)

def resize_disk(proxmox_ip, proxmox_node, token_name, token_secret, vmid_to_use, vm_storage):
    endpoint=f"api2/json/nodes/{proxmox_node}/qemu{vmid_to_use}/resize"
    data={}
    data["disk"]="virtio0"
    data["size"]=f"{vm_storage}G"
    put_cluster_query(endpoint, data, proxmox_ip, token_name, token_secret)

def create_box(proxmox_ip, proxmox_node, proxmox_pool, token_name, token_secret, low_vmid, high_vmid, template_name, vm_name, vm_role, vm_cores, vm_memory, vm_storage, vm_network):
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
    print(f"Ensuring the resource pool {proxmox_pool} exists")
    ensure_resource_pool(proxmox_ip, token_name, token_secret, proxmox_pool)
    clone_template(proxmox_ip, proxmox_node, token_name, token_secret, template_vmid, vmid_to_use, vm_name, proxmox_pool)
    configure_vm(proxmox_ip, proxmox_node, token_name, token_secret, vmid_to_use, vm_cores, vm_memory, vm_network)
    resize_disk(proxmox_ip, proxmox_node, token_name, token_secret, vmid_to_use, vm_storage)

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
    parser.add_argument("--vm_name", required=True, help="The name of the VM to create")
    parser.add_argument("--vm_role", required=True, help="The role of the VM to create")
    parser.add_argument("--vm_cores", required=True, help="Number of cores for the VM")
    parser.add_argument("--vm_memory", required=True, help="Memory for the VM")
    parser.add_argument("--vm_storage", required=True, help="Amount of storage, in GB")
    parser.add_argument("--vm_network", required=True, help="interface to attach to the VM")

    args = parser.parse_args()
    proxmox_ip      = args.proxmox_ip
    proxmox_node    = args.proxmox_node
    proxmox_pool    = args.proxmox_pool
    token_name      = args.token_name
    token_secret    = args.token_secret
    low_vmid        = args.low_vmid
    high_vmid       = args.high_vmid
    template_name   = args.template_name
    vm_name         = args.vm_name
    vm_role         = args.vm_role
    vm_cores        = args.vm_cores
    vm_memory       = args.vm_memory
    vm_storage      = args.vm_storage
    vm_network      = args.vm_network
    
    create_box(proxmox_ip, proxmox_node, proxmox_pool, token_name, token_secret, low_vmid, high_vmid, template_name, vm_name, vm_role, vm_cores, vm_memory, vm_storage, vm_network)


if __name__ == "__main__":
    main()