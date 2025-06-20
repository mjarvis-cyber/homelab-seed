import argparse
import json
import paramiko
import re
from ipaddress import ip_network, ip_address
import os

def load_private_key(path):
    from paramiko import RSAKey, ECDSAKey, Ed25519Key, DSSKey
    for key_cls in [Ed25519Key, RSAKey, ECDSAKey, DSSKey]:
        try:
            return key_cls.from_private_key_file(path)
        except Exception:
            continue
    raise ValueError(f"Unsupported or unreadable private key: {path}")

def get_network_info(master_ip, ssh_key_path, ssh_user):
    key = load_private_key(ssh_key_path)
    print(f"Using SSH key type: {type(key).__name__}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(master_ip, username=ssh_user, pkey=key)
    
    stdin, stdout, stderr = ssh.exec_command('ip addr show')
    network_info = stdout.read().decode()
    ssh.close()
    
    ip_addresses = []
    for line in network_info.splitlines():
        if 'inet ' in line:
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', line)
            if match:
                ip = match.group(1)
                subnet_mask = int(match.group(2))
                ip_addresses.append((ip, subnet_mask))
    
    return ip_addresses

def find_matching_ip(vm_ipv4, network_info):
    vm_ip = ip_address(vm_ipv4)
    for ip, subnet_mask in network_info:
        network = ip_network(f"{ip}/{subnet_mask}", strict=False)
        if vm_ip in network:
            return ip
    return None

def scp_directory_to_remote(ssh_key_path, path_to_scp, remote_host, username='ubuntu'):
    key = load_private_key(ssh_key_path)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(remote_host, username=username, pkey=key)
    
    put_path = f"/home/{username}"
    
    # List files in the directory before copying
    print(f"Files in {path_to_scp}:")
    for root, dirs, files in os.walk(path_to_scp):
        for file in files:
            file_path = os.path.join(root, file)
            print(file_path)
    
    scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    
    # Copy the specific files (install.sh and Dockerfile in this case)
    scp.put(f"{path_to_scp}/install.sh", f"{put_path}/install.sh")
    scp.put(f"{path_to_scp}/Dockerfile", f"{put_path}/Dockerfile")
    
    scp.close()
    ssh.close()

def run_remote_command(ssh_key_path, remote_host, master_ip, agent_name, secret, docker_registry, username='ubuntu'):
    makeexec = f"chmod +x /home/{username}/install.sh"
    command = f"sudo /home/{username}/install.sh -i {master_ip} -p 8080 -n {agent_name} -s {secret} -d {docker_registry} -u {username}"
    key = load_private_key(ssh_key_path)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(remote_host, username=username, pkey=key)
    stdin, stdout, stderr = ssh.exec_command(makeexec)
    stdin, stdout, stderr = ssh.exec_command(command)
    print(stdout.read().decode())
    print(stderr.read().decode())
    ssh.close()

def main():
    parser = argparse.ArgumentParser(description='Provision a Jenkins agent.')
    parser.add_argument('--secret-file', required=True, help='Path to the secret file.')
    parser.add_argument('--metadata-file', required=True, help='Path to the VM metadata JSON file.')
    parser.add_argument('--ssh-key-file', required=True, help='Path to the SSH private key file.')
    parser.add_argument('--scp-dir', required=True, help='Path to the directory to SCP.')
    parser.add_argument('--agent-name', required=True, help='Name of the Jenkins agent.')
    parser.add_argument('--master-ip', required=True, help='IP address of the Jenkins master.')
    parser.add_argument('--docker-registry', required=True, help='URL of docker registry to trust.')
    parser.add_argument('--ssh-user', default='ubuntu', help='SSH username to connect to the target VM')

    args = parser.parse_args()
    with open(args.metadata_file) as f:
        metadata = json.load(f)

    vm_ipv4 = metadata['vm_ipv4']

    with open(args.secret_file) as f:
        secret = f.read().strip()
    if os.path.exists(args.ssh_key_file):
        print("File exists")
        with open(args.ssh_key_file, "r") as file:
            print(file.readline(), end="")
            print(file.readline(), end="")
    else:
        print("File does not exist")
    network_info = get_network_info(args.master_ip, args.ssh_key_file, args.ssh_user)
    master_ip = find_matching_ip(vm_ipv4, network_info)
    if not master_ip:
        print("No matching IP found in the same subnet.")
        return
    scp_directory_to_remote(args.ssh_key_file, args.scp_dir, vm_ipv4, args.ssh_user)
    run_remote_command(args.ssh_key_file, vm_ipv4, master_ip, args.agent_name, secret, args.docker_registry, args.ssh_user)

if __name__ == "__main__":
    main()
