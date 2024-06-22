from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import requests
import json
import argparse
import os
import shutil
import paramiko
from scp import SCPClient
import uuid
import time
import urllib.parse

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

def generate_public_key(private_key_path, public_key_path):
    try:
        with open(private_key_path, "rb") as key_file:
            private_key_data = key_file.read()
            print(f"Private Key (start): {private_key_data[:30]}")
            print(f"Private Key (mid): {private_key_data[len(private_key_data)//2 - 15:len(private_key_data)//2 + 15]}")
            print(f"Private Key (end): {private_key_data[-30:]}")
        
        with open(private_key_path, "r") as key_file:
            private_key = paramiko.RSAKey.from_private_key(key_file)
        
        pem_data = private_key.key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        private_key = serialization.load_pem_private_key(
            pem_data,
            password=None,
            backend=default_backend()
        )
    
        public_key = private_key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH
        )
    
        with open(public_key_path, 'a') as pub_key_file:
            pub_key_file.write("\n")
            pub_key_file.write(public_key.decode('utf-8'))
            pub_key_file.write("\n")
    
        print(f"Public key written to {public_key_path}")
        return public_key
    except Exception as e:
        print(f"Error loading private key: {e}")
        raise

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

def create_ssh_client(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def upload_qcow(proxmox_ip, proxmox_node, user, password, qcow_file, remote_dir, vmid, name):
    remote_filename=f"{remote_dir}/{name}.qcow2"
    ssh = create_ssh_client(proxmox_ip, 22, user, password)
    scp = SCPClient(ssh.get_transport())
    
    stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_dir}')
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(f"Failed to create directory {remote_dir} on {proxmox_ip}")
        return
    
    scp.put(qcow_file, remote_path=remote_filename)
    ssh.exec_command(f"qm importdisk {vmid} {remote_filename} local-lvm")
    scp.close()
    ssh.close()

def configure_disk(proxmox_ip, proxmox_node, token_name, token_secret, vmid):
    endpoint=f"api2/json/nodes/{proxmox_node}/qemu/{vmid}/config"
    data=f"scsihw=virtio-scsi-pci&virtio0=local-lvm:vm-{vmid}-disk-0&serial0=socket&boot=c&bootdisk=virtio0"
    put_cluster_query(endpoint, data, proxmox_ip, token_name, token_secret)

def configure_cloud_init(proxmox_ip, proxmox_node, token_name, token_secret, vmid, user, password, public_key_path):
    endpoint = f"api2/json/nodes/{proxmox_node}/qemu/{vmid}/config"

    with open(public_key_path, 'r') as file:
        public_keys = file.read().strip()

    data = f"agent=1&ide2=local-lvm:cloudinit&ciuser={user}&cipassword={password}"
    put_cluster_query(endpoint, data, proxmox_ip, token_name, token_secret)
    # ssh keys are weird to manage
    sshKey = quote(public_keys, safe='')
    data={}
    data["sshkeys"] = sshKey
    put_cluster_query(endpoint, data, proxmox_ip, token_name, token_secret)

def create_vm(proxmox_ip, proxmox_node, token_name, token_secret, vmid, name):
    endpoint=f"api2/json/nodes/{proxmox_node}/qemu"
    data=f"vmid={vmid}&name={name}&cores=2&memory=2048&onboot=1&vga=qxl&hotplug=disk,network,usb"
    post_cluster_query(endpoint, data, proxmox_ip, token_name, token_secret)

def vm_creation_pipeline(proxmox_ip, proxmox_node, token_name, token_secret, vmid, name, image_url, ssh_keys, qcow_dir, user, password, proxmox_user, proxmox_password, ip_to_use, template_ssh_key):
    remote_dir="/root/qcows"
    qcow_file = f"{qcow_dir}/{name}.qcow2"

    print("Generate public key from private key")
    public_key = generate_public_key(template_ssh_key, ssh_keys)
    print(f"Generated public key: {public_key}")

    print(f"Getting cloud image from {image_url} and placing in {qcow_file}")
    get_qcow(image_url, qcow_dir, qcow_file, name)

    print(f"Creating VM {name} with VMID: {vmid}")
    create_vm(proxmox_ip, proxmox_node, token_name, token_secret, vmid, name)

    print(f"Uploading {qcow_file} to proxmox")
    print("Uploading the qcow, this could take a while")
    upload_qcow(proxmox_ip, proxmox_node, proxmox_user, proxmox_password, qcow_file, remote_dir, vmid, name)
    time.sleep(15)
    os.remove(qcow_file)
    print("Configuring disk on template")
    configure_disk(proxmox_ip, proxmox_node, token_name, token_secret, vmid)

    print("Configuring cloud-init")
    configure_cloud_init(proxmox_ip, proxmox_node, token_name, token_secret, vmid, user, password, ssh_keys)



def runner(proxmox_ip, proxmox_node, token_name, token_secret, resource_pool_name, name, vmid_start, vmid_end, qcow_dir, ssh_keys, image_location, user, password, proxmox_user, proxmox_password, ip_to_use, template_ssh_key):
    vmid = pick_vmid(proxmox_ip, token_name, token_secret, vmid_start, vmid_end)
    print(f"Here is the vmid to use: {vmid}")
    vm_creation_pipeline(proxmox_ip, proxmox_node, token_name, token_secret, vmid, name, image_location, ssh_keys, qcow_dir, user, password, proxmox_user, proxmox_password, ip_to_use, template_ssh_key)

def main():
    parser = argparse.ArgumentParser(description="Create Proxmox templates")
    parser.add_argument("--proxmox_ip", required=True, help="Proxmox IP address")
    parser.add_argument("--proxmox_node", required=True, help="Proxmox host to build the template on")
    parser.add_argument("--token_name", required=True, help="Proxmox API token name")
    parser.add_argument("--token_secret", required=True, help="Proxmox API token secret")
    parser.add_argument("--user", required=True, help="Proxmox SSH user")
    parser.add_argument("--password", required=True, help="Proxmox SSH password")
    parser.add_argument("--template_ssh_key", required=True, help="Path to the private SSH key")

    args = parser.parse_args()

    proxmox_ip = args.proxmox_ip
    proxmox_node = args.proxmox_node
    token_name = args.token_name
    token_secret = args.token_secret
    proxmox_user = args.user
    proxmox_password = args.password
    template_ssh_key = args.template_ssh_key
    print(f"The ssh key: {template_ssh_key}")

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
            proxmox_user,
            proxmox_password,
            config['temporary_ip'],
            template_ssh_key
        )

if __name__ == "__main__":
    main()
